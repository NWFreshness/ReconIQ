"use client";

import { useState, useEffect } from "react";
import { X, Check, List } from "lucide-react";
import Link from "next/link";
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
      <button
        onClick={() => setShowModal(true)}
        className={`btn px-2 ${inListCount > 0 ? "border-accent text-accent" : ""}`}
        title="Manage lists"
        aria-label="Manage lists"
      >
        <List className="w-3.5 h-3.5" />
        {inListCount > 0 ? inListCount : ""}
      </button>

      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowModal(false);
          }}
        >
          <div role="dialog" aria-modal="true" aria-label="Manage lists" className="bg-background border border-foreground p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-xl font-semibold">Manage lists</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-muted hover:text-foreground transition-colors"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {error && <div className="mb-3 notice-danger">{error}</div>}

            <div className="mb-5 space-y-2">
              <p className="sub-label">Create a list</p>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="List name"
                aria-label="List name"
                className="field"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && newName.trim()) handleCreateList();
                }}
              />
              <input
                type="text"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Description (optional)"
                aria-label="Description"
                className="field"
              />
              <button
                onClick={handleCreateList}
                disabled={loading || !newName.trim()}
                className="btn btn-primary w-full py-2"
              >
                {loading ? "Creating..." : "Create list and add analysis"}
              </button>
            </div>

            <div className="max-h-60 overflow-y-auto border-t border-border">
              {lists.length === 0 ? (
                <p className="text-xs text-muted py-4">No lists yet. Create one above.</p>
              ) : (
                lists.map((list) => {
                  const isInList = currentListIds.includes(list.id);
                  return (
                    <div key={list.id} className="flex items-center justify-between gap-3 py-2.5 border-b border-border">
                      <div className="min-w-0">
                        <Link
                          href={`/lists/${list.id}`}
                          className="text-sm font-medium truncate block hover:text-accent hover:underline"
                        >
                          {list.name}
                        </Link>
                        <span className="text-xs text-muted">{list.analysis_count} analyses</span>
                      </div>
                      {isInList ? (
                        <button
                          onClick={() => handleRemoveFromList(list.id)}
                          className="btn border-success text-success"
                        >
                          <Check className="w-3 h-3" />
                          In list
                        </button>
                      ) : (
                        <button onClick={() => handleAddToList(list.id)} className="btn">
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
