"use client";

import { useState, useEffect } from "react";
import { FolderPlus, FolderOpen, X, Check, List } from "lucide-react";
import { prospectLists, type ProspectList } from "@/lib/api";

interface ListManagerProps {
  analysisId: string;
  currentListIds: string[];
  onListsChange?: (listIds: string[]) => void;
}

export function ListManager({ analysisId, currentListIds, onListsChange }: ListManagerProps) {
  const [lists, setLists] = useState<ProspectList[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void prospectLists.list().then(setLists).catch(() => {});
  }, []);

  const handleAddToList = async (listId: string) => {
    try {
      await prospectLists.addAnalysis(listId, analysisId);
      setLists((prev) =>
        prev.map((l) =>
          l.id === listId ? { ...l, analysis_count: l.analysis_count + 1 } : l
        )
      );
      onListsChange?.([...currentListIds, listId]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add to list");
    }
  };

  const handleRemoveFromList = async (listId: string) => {
    try {
      await prospectLists.removeAnalysis(listId, analysisId);
      setLists((prev) =>
        prev.map((l) =>
          l.id === listId
            ? { ...l, analysis_count: Math.max(0, l.analysis_count - 1) }
            : l
        )
      );
      onListsChange?.(currentListIds.filter((id) => id !== listId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove from list");
    }
  };

  const handleCreateList = async () => {
    if (!newName.trim()) return;
    setLoading(true);
    setError("");
    try {
      const created = await prospectLists.create(newName.trim(), newDesc.trim() || undefined);
      setLists((prev) => [created, ...prev]);
      // Also add the analysis to the new list
      await prospectLists.addAnalysis(created.id, analysisId);
      onListsChange?.([...currentListIds, created.id]);
      setNewName("");
      setNewDesc("");
      setShowModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create list");
    } finally {
      setLoading(false);
    }
  };

  const inListCount = currentListIds.length;

  return (
    <>
      {/* Inline list assignment dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowModal(true)}
          className={`text-xs px-2 py-1.5 rounded-lg border transition-colors flex items-center gap-1.5 ${
            inListCount > 0
              ? "bg-amber-400/10 text-amber-400 border-amber-400/30 hover:bg-amber-400/20"
              : "bg-surface-hover text-muted border-border hover:text-foreground hover:border-muted"
          }`}
          title="Manage lists"
        >
          <List className="w-3 h-3" />
          {inListCount > 0 ? inListCount : ""}
        </button>
      </div>

      {/* Modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowModal(false);
          }}
        >
          <div className="bg-surface border border-border rounded-xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground">Manage Lists</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-muted hover:text-foreground transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {error && (
              <div className="mb-3 text-xs text-red-400 bg-red-400/5 border border-red-400/10 rounded-lg p-2">
                {error}
              </div>
            )}

            {/* Create new list */}
            <div className="mb-4 p-3 bg-background border border-border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <FolderPlus className="w-3.5 h-3.5 text-muted" />
                <span className="text-xs font-medium text-foreground">Create new list</span>
              </div>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="List name..."
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-xs text-foreground placeholder:text-muted focus:outline-none focus:border-amber-500/50 mb-2"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && newName.trim()) handleCreateList();
                }}
              />
              <input
                type="text"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Description (optional)"
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-xs text-foreground placeholder:text-muted focus:outline-none focus:border-amber-500/50 mb-2"
              />
              <button
                onClick={handleCreateList}
                disabled={loading || !newName.trim()}
                className="w-full px-3 py-2 bg-accent/10 text-accent border border-accent/30 rounded-lg text-xs font-medium hover:bg-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Creating..." : "Create & add analysis"}
              </button>
            </div>

            {/* Existing lists */}
            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              {lists.length === 0 ? (
                <p className="text-xs text-muted text-center py-4">No lists yet. Create one above.</p>
              ) : (
                lists.map((list) => {
                  const isInList = currentListIds.includes(list.id);
                  return (
                    <div
                      key={list.id}
                      className="flex items-center justify-between px-3 py-2 rounded-lg bg-background border border-border hover:border-muted transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <FolderOpen className="w-3.5 h-3.5 text-muted flex-shrink-0" />
                        <div className="min-w-0">
                          <span className="text-xs font-medium text-foreground truncate block">
                            {list.name}
                          </span>
                          <span className="text-[10px] text-muted">{list.analysis_count} analyses</span>
                        </div>
                      </div>
                      {isInList ? (
                        <button
                          onClick={() => handleRemoveFromList(list.id)}
                          className="text-xs px-2 py-1 rounded bg-emerald-400/10 text-emerald-400 border border-emerald-400/30 hover:bg-emerald-400/20 transition-colors flex items-center gap-1"
                        >
                          <Check className="w-3 h-3" />
                          In list
                        </button>
                      ) : (
                        <button
                          onClick={() => handleAddToList(list.id)}
                          className="text-xs px-2 py-1 rounded bg-surface-hover text-muted border border-border hover:text-foreground hover:border-muted transition-colors"
                        >
                          Add
                        </button>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
