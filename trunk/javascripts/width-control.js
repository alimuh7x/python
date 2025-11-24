// Width control functionality
(function() {
    'use strict';

    // Create width control widget
    function createWidthControl() {
        // Find the header element
        const header = document.querySelector('.md-header');
        if (!header) return;

        const container = document.createElement('div');
        container.className = 'width-control-container';

        const control = document.createElement('div');
        control.className = 'width-control';
        control.innerHTML = `
            <button data-width="narrow" title="Narrow width (1400px)">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="7" y="4" width="10" height="16" rx="1"/>
                </svg>
            </button>
            <button data-width="medium" title="Medium width (1600px)" class="active">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="4" y="4" width="16" height="16" rx="1"/>
                </svg>
            </button>
            <button data-width="wide" title="Full width">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="4" width="20" height="16" rx="1"/>
                </svg>
            </button>
        `;

        container.appendChild(control);
        header.appendChild(container);

        // Load saved preference
        const savedWidth = localStorage.getItem('content-width') || 'medium';
        setWidth(savedWidth);

        // Add click handlers
        control.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', function() {
                const width = this.getAttribute('data-width');
                setWidth(width);
                localStorage.setItem('content-width', width);
            });
        });
    }

    // Set width mode
    function setWidth(width) {
        document.body.setAttribute('data-width', width);

        // Update active button
        document.querySelectorAll('.width-control button').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-width') === width) {
                btn.classList.add('active');
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidthControl);
    } else {
        createWidthControl();
    }

    // Reinitialize on navigation (for Material for MkDocs instant loading)
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof document$ !== 'undefined') {
            document$.subscribe(function() {
                const savedWidth = localStorage.getItem('content-width') || 'medium';
                setWidth(savedWidth);
            });
        }
    });
})();
