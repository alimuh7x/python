// Initialize and render mermaid diagrams
document.addEventListener('DOMContentLoaded', function() {
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default'
    });
  }
});

// For Material theme with instant loading
if (typeof document$ !== 'undefined') {
  document$.subscribe(function() {
    if (typeof mermaid !== 'undefined') {
      mermaid.contentLoaded();
    }
  });
}
