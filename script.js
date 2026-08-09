// Simple interactivity for the games website

document.addEventListener('DOMContentLoaded', () => {
    // We removed the e.preventDefault() so the links actually work now!
    // But we can still add a small sound or effect if we wanted to.

    // Add click effect to CTA button
    const ctaBtn = document.querySelector('.cta-button');
    if(ctaBtn) {
        ctaBtn.addEventListener('click', () => {
            const gamesSection = document.querySelector('.games-section');
            gamesSection.scrollIntoView({ behavior: 'smooth' });
        });
    }
});
