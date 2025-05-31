import { create } from 'zustand';
import { Instance, ComparisonResult } from '../types';

interface AppState {
  // Instances
  instances: Instance[];
  selectedSourceInstance: Instance | null;
  selectedDestInstance: Instance | null;
  loadingInstances: boolean;
  
  // Comparison
  comparisonResult: ComparisonResult | null;
  loadingComparison: boolean;
  selectedItems: string[];
  
  // UI State
  snackbar: {
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  };
  
  // Actions
  setInstances: (instances: Instance[]) => void;
  setSelectedSourceInstance: (instance: Instance | null) => void;
  setSelectedDestInstance: (instance: Instance | null) => void;
  setLoadingInstances: (loading: boolean) => void;
  
  setComparisonResult: (result: ComparisonResult | null) => void;
  setLoadingComparison: (loading: boolean) => void;
  toggleItemSelection: (identifier: string) => void;
  selectAllItems: (identifiers: string[]) => void;
  clearSelectedItems: () => void;
  
  showSnackbar: (message: string, severity: 'success' | 'error' | 'warning' | 'info') => void;
  hideSnackbar: () => void;
}

const useStore = create<AppState>((set) => ({
  // Initial state
  instances: [],
  selectedSourceInstance: null,
  selectedDestInstance: null,
  loadingInstances: false,
  
  comparisonResult: null,
  loadingComparison: false,
  selectedItems: [],
  
  snackbar: {
    open: false,
    message: '',
    severity: 'info',
  },
  
  // Actions
  setInstances: (instances) => set({ instances }),
  setSelectedSourceInstance: (instance) => set({ selectedSourceInstance: instance }),
  setSelectedDestInstance: (instance) => set({ selectedDestInstance: instance }),
  setLoadingInstances: (loading) => set({ loadingInstances: loading }),
  
  setComparisonResult: (result) => set({ comparisonResult: result }),
  setLoadingComparison: (loading) => set({ loadingComparison: loading }),
  
  toggleItemSelection: (identifier) => set((state) => ({
    selectedItems: state.selectedItems.includes(identifier)
      ? state.selectedItems.filter(id => id !== identifier)
      : [...state.selectedItems, identifier]
  })),
  
  selectAllItems: (identifiers) => set({ selectedItems: identifiers }),
  clearSelectedItems: () => set({ selectedItems: [] }),
  
  showSnackbar: (message, severity) => set({
    snackbar: { open: true, message, severity }
  }),
  
  hideSnackbar: () => set((state) => ({
    snackbar: { ...state.snackbar, open: false }
  })),
}));

export default useStore;