// EMERGENCY SIMPLE NAVIGATION - GUARANTEED TO WORK
function showPage(pageId) {
    console.log('🚨 SIMPLE showPage called:', pageId);
    
    // Hide ALL pages
    const allPages = document.querySelectorAll('.page');
    allPages.forEach(page => {
        page.style.display = 'none';
        page.classList.remove('active');
    });
    
    // Show the target page
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.style.display = 'block';
        targetPage.classList.add('active');
        console.log('✅ Page shown:', pageId);
    } else {
        console.error('❌ Page not found:', pageId);
    }
    
    // Update nav items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    
    const activeNavItem = document.querySelector(`[onclick*="showPage('${pageId}')"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
        console.log('✅ Nav updated for:', pageId);
    }
}

// Force initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚨 EMERGENCY navigation initialized');
    // Show dashboard by default
    setTimeout(() => showPage('dashboard'), 100);
});