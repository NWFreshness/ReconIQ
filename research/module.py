"""Registry + Template Method Pattern for Research Modules.

Before this refactor, each research module (company_profile, seo_keywords,
competitors, etc.) duplicated identical boilerplate and the coordinator
maintained a hard-coded dispatch table for module names, labels, and ordering.

Solution — two complementary patterns:

1. REGISTRY PATTERN
   Modules register with ModuleRegistry, declaring their name, label,
   dependencies, and execution order. The coordinator queries the registry
   instead of maintaining its own dispatch table. Adding a new module =
   one registry entry or @research_module decorator, zero coordinator changes.

2. TEMPLATE METHOD PATTERN (for new/refactored modules)
   BaseResearchModule.execute() defines the skeleton:
       build_prompt() → call_llm() → process_result() → validate
   Subclasses override hooks without duplicating boilerplate. All evidence
   attachment, schema validation, and error handling lives in the base class.

Current state:
  - Existing modules (company_profile, seo_keywords, etc.) use their run()
    functions directly → registered via ModuleRegistry.register_existing().
  - Future modules can use @research_module + BaseResearchModule subclass.
  - ModuleRegistry provides the catalog/ordering the coordinator needs.
"""

from __future__ import annotations

import abc
import dataclasses
from typing import Any, Callable, ClassVar, Optional

from scraper.models import ScrapeResult

# ── Module descriptor (Registry entry) ─────────────────────────────────────


@dataclasses.dataclass
class ModuleDescriptor:
    """Metadata about a registered research module."""

    name: str  # key in results dict, e.g. "company_profile"
    label: str  # human-readable, e.g. "Company Profile"
    cls: Optional[type["BaseResearchModule"]] = None
    dependencies: tuple[str, ...] = ()  # module names that must run first
    order: int = 0  # lower = earlier in pipeline
    downstream_group: str | None = None  # "parallel_downstream", "synthesis", etc.


# ── Module Registry ────────────────────────────────────────────────────────


class ModuleRegistry:
    """Central registry of all research modules.

    Two registration paths:
      a) ModuleRegistry.register_existing(name, label, ...) — for function-based
         modules that don't use the decorator pattern. Called at import time.
      b) @research_module decorator — for class-based modules. Registration
         happens automatically when the module file is imported.

    The coordinator queries this registry for module discovery and ordering.
    """

    _modules: ClassVar[dict[str, ModuleDescriptor]] = {}

    @classmethod
    def register_existing(
        cls,
        name: str,
        label: str,
        dependencies: tuple[str, ...] = (),
        order: int = 0,
        downstream_group: str | None = None,
    ) -> None:
        """Register a module that doesn't use the @research_module decorator.

        Idempotent — calling twice with the same name is a no-op.
        Use this for backward compatibility with existing run() function-based
        modules until they are converted to BaseResearchModule subclasses.
        """
        if name in cls._modules:
            return
        cls._modules[name] = ModuleDescriptor(
            name=name,
            label=label,
            dependencies=dependencies,
            order=order,
            downstream_group=downstream_group,
        )

    @classmethod
    def _register_decorated(
        cls,
        name: str,
        label: str,
        module_cls: type["BaseResearchModule"],
        dependencies: tuple[str, ...] = (),
        order: int = 0,
        downstream_group: str | None = None,
    ) -> None:
        """Register a class-based module (called by @research_module decorator)."""
        if name in cls._modules:
            raise ValueError(f"Module '{name}' is already registered")
        cls._modules[name] = ModuleDescriptor(
            name=name,
            label=label,
            cls=module_cls,
            dependencies=dependencies,
            order=order,
            downstream_group=downstream_group,
        )

    @classmethod
    def get(cls, name: str) -> Optional["BaseResearchModule"]:
        """Get an initialized module instance by name (class-based only)."""
        desc = cls._modules.get(name)
        if desc is None or desc.cls is None:
            return None
        return desc.cls()

    @classmethod
    def get_descriptor(cls, name: str) -> Optional[ModuleDescriptor]:
        return cls._modules.get(name)

    @classmethod
    def list_all(cls) -> list[ModuleDescriptor]:
        """All registered modules, sorted by execution order."""
        return sorted(cls._modules.values(), key=lambda d: d.order)

    @classmethod
    def list_by_group(cls, group: str) -> list[ModuleDescriptor]:
        """Modules belonging to a specific downstream group."""
        return sorted(
            [d for d in cls._modules.values() if d.downstream_group == group],
            key=lambda d: d.order,
        )

    @classmethod
    def get_labels(cls) -> dict[str, str]:
        """Module name → human-readable label mapping."""
        return {name: desc.label for name, desc in cls._modules.items()}

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name in cls._modules

    @classmethod
    def ensure_initialized(cls) -> None:
        """Ensure all modules are registered.

        Registers existing function-based modules explicitly, then imports
        any decorated module files.
        """
        # Register existing function-based modules
        cls.register_existing(
            "company_profile", "Company Profile",
            order=10, downstream_group="primary",
        )
        cls.register_existing(
            "seo_keywords", "SEO Keywords",
            dependencies=("company_profile",), order=20,
            downstream_group="parallel_downstream",
        )
        cls.register_existing(
            "competitor", "Competitor Intel",
            dependencies=("company_profile",), order=20,
            downstream_group="parallel_downstream",
        )
        cls.register_existing(
            "social_content", "Social Content",
            dependencies=("company_profile",), order=20,
            downstream_group="parallel_downstream",
        )
        cls.register_existing(
            "swot", "SWOT Synthesis",
            dependencies=("company_profile", "seo_keywords", "competitor", "social_content"),
            order=40, downstream_group="synthesis",
        )
        cls.register_existing(
            "outreach", "Outreach Pack",
            dependencies=("swot",), order=50, downstream_group="synthesis",
        )
        cls.register_existing(
            "prospect_score", "Prospect Score",
            dependencies=("company_profile",), order=60, downstream_group="scoring",
        )

        # Import decorated modules (future-proof — @research_module triggers
        # _register_decorated on import)
        try:
            pass  # No decorated modules yet — placeholder
        except ImportError:
            pass


# ── Decorator for self-registration ────────────────────────────────────────


def research_module(
    *,
    name: str,
    label: str,
    required_keys: Optional[list[str]] = None,
    schema_class: Optional[type] = None,
    dependencies: tuple[str, ...] = (),
    order: int = 0,
    downstream_group: str | None = None,
    max_tokens: int = 2048,
):
    """Class decorator: register a research module with the ModuleRegistry.

    Usage:
        @research_module(
            name="company_profile",
            label="Company Profile",
            required_keys=["company_name", "what_they_do", ...],
            schema_class=CompanyProfileSchema,
            order=10,
        )
        class CompanyProfileModule(BaseResearchModule):
            ...

    The decorator:
      1. Injects required_keys, schema_class, max_tokens onto the class
      2. Registers the class with ModuleRegistry
    """

    def decorator(cls: type[BaseResearchModule]):
        cls.required_keys = required_keys or []
        cls.schema_class = schema_class
        cls.max_tokens = max_tokens
        ModuleRegistry._register_decorated(
            name=name,
            label=label,
            module_cls=cls,
            dependencies=dependencies,
            order=order,
            downstream_group=downstream_group,
        )
        return cls

    return decorator


# ── Base class with Template Method ────────────────────────────────────────


class BaseResearchModule(abc.ABC):
    """Template Method base for new/refactored research modules.

    Subclasses override hooks (build_prompt, get_system_prompt, etc.)
    but never touch execute() — the skeleton is fixed.

    The skeleton:
      1. build_prompt(inputs, scrape_result) → str
      2. call_llm(prompt) → dict  (handles JSON parsing, retries)
      3. process_result(data, inputs, scrape_result) → dict
      4. return validated dict

    Class attributes (set by @research_module decorator):
      required_keys: list[str]
      schema_class: Pydantic model class
      max_tokens: int
    """

    required_keys: ClassVar[list[str]] = []
    schema_class: ClassVar[Optional[type]] = None
    max_tokens: ClassVar[int] = 2048

    def __init__(self):
        self._llm_complete: Optional[Callable] = None

    # ── Template Method (final — subclasses do NOT override) ──────────────

    def execute(
        self,
        inputs: dict[str, Any],
        llm_complete: Callable,
        scrape_result: ScrapeResult | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Run this research module end-to-end. Subclasses do NOT override.

        Args:
            inputs: Dict of upstream module outputs keyed by module name.
            llm_complete: LLM completion callable.
            scrape_result: Structured scrape output (optional).
            **kwargs: Passed to build_prompt and process_result hooks.

        Returns:
            Validated dict matching this module's schema.
        """
        self._llm_complete = llm_complete
        prompt = self.build_prompt(inputs, scrape_result, **kwargs)
        data = self._call_llm(prompt)
        data = self.process_result(data, inputs, scrape_result, **kwargs)
        return self._validate(data)

    # ── Hooks (subclasses override these) ──────────────────────────────────

    @abc.abstractmethod
    def build_prompt(
        self,
        inputs: dict[str, Any],
        scrape_result: ScrapeResult | None,
        **kwargs,
    ) -> str:
        """Build the LLM prompt from upstream inputs."""
        ...

    def get_system_prompt(self) -> str:
        """Return the system prompt for this module's LLM call."""
        return ""

    def process_result(
        self,
        data: dict[str, Any],
        inputs: dict[str, Any],
        scrape_result: ScrapeResult | None,
        **kwargs,
    ) -> dict[str, Any]:
        """Post-process LLM output. Default: attaches scrape evidence."""
        from research.evidence import attach_evidence, collect_scrape_evidence

        attach_evidence(
            data, collect_scrape_evidence(scrape_result, module=self.module_name())
        )
        return data

    def module_name(self) -> str:
        """Machine-readable module name. Override if needed."""
        return self.__class__.__name__

    # ── Internal ──────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str) -> dict[str, Any]:
        from research.parsing import llm_json_call

        return llm_json_call(
            llm_complete=self._llm_complete,
            prompt=prompt,
            module=self.module_name(),
            system=self.get_system_prompt(),
            required_keys=self.required_keys,
            context=self.module_name(),
            max_tokens=self.max_tokens,
        )

    def _validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.schema_class is None:
            return data
        from research.schemas import validate_module_output

        return validate_module_output(data, self.schema_class, self.module_name())


# ── Helper for building module inputs dict ─────────────────────────────────


def build_inputs_dict(
    results: dict[str, Any], module_names: list[str]
) -> dict[str, Any]:
    """Extract upstream module outputs into the format execute() expects."""
    return {name: results.get(name, {}) for name in module_names}
