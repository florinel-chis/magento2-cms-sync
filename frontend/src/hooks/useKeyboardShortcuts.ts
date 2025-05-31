import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function useKeyboardShortcuts() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      // Only handle shortcuts when not typing in an input
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        event.target instanceof HTMLSelectElement
      ) {
        return;
      }

      // Alt/Option + number shortcuts for navigation
      if (event.altKey) {
        switch (event.key) {
          case '1':
            event.preventDefault();
            navigate('/instances');
            break;
          case '2':
            event.preventDefault();
            navigate('/compare-blocks');
            break;
          case '3':
            event.preventDefault();
            navigate('/compare-pages');
            break;
          case '4':
            event.preventDefault();
            navigate('/sync');
            break;
          case '5':
            event.preventDefault();
            navigate('/history');
            break;
        }
      }

      // Ctrl/Cmd + K for search focus (if implemented)
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        // This could focus a global search input if implemented
        const searchInput = document.querySelector('[data-search-input]');
        if (searchInput instanceof HTMLInputElement) {
          searchInput.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [navigate]);
}