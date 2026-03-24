import { create } from "zustand";
import { persist } from "zustand/middleware";

interface BookmarkStore {
  bookmarkedIds: Set<number>;
  toggle: (rallyId: number) => void;
  isBookmarked: (rallyId: number) => boolean;
  count: () => number;
  clear: () => void;
}

export const useBookmarkStore = create<BookmarkStore>()(
  persist(
    (set, get) => ({
      bookmarkedIds: new Set<number>(),

      toggle: (rallyId) =>
        set((state) => {
          const next = new Set(state.bookmarkedIds);
          if (next.has(rallyId)) {
            next.delete(rallyId);
          } else {
            next.add(rallyId);
          }
          return { bookmarkedIds: next };
        }),

      isBookmarked: (rallyId) => get().bookmarkedIds.has(rallyId),

      count: () => get().bookmarkedIds.size,

      clear: () => set({ bookmarkedIds: new Set() }),
    }),
    {
      name: "ishuttle-bookmarks",
      // Set은 JSON 직렬화 불가 → 배열로 변환
      storage: {
        getItem: (name) => {
          const raw = localStorage.getItem(name);
          if (!raw) return null;
          const parsed = JSON.parse(raw);
          return {
            ...parsed,
            state: {
              ...parsed.state,
              bookmarkedIds: new Set<number>(parsed.state.bookmarkedIds ?? []),
            },
          };
        },
        setItem: (name, value) => {
          const serialized = {
            ...value,
            state: {
              ...value.state,
              bookmarkedIds: Array.from(value.state.bookmarkedIds),
            },
          };
          localStorage.setItem(name, JSON.stringify(serialized));
        },
        removeItem: (name) => localStorage.removeItem(name),
      },
    }
  )
);
