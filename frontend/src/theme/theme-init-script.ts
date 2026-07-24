/**
 * Inline script to apply theme before paint and reduce flash.
 * Keep in sync with THEME_STORAGE_KEY / resolveTheme.
 */
export const themeInitScript = `(function(){try{var k='safetymain.theme-mode';var m=localStorage.getItem(k);var d=window.matchMedia('(prefers-color-scheme: dark)').matches;var r=(m==='light'||m==='dark')?m:(d?'dark':'light');document.documentElement.setAttribute('data-theme',r);}catch(e){}})();`;
