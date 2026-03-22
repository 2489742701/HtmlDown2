function setWebExeConfig(options) {
    window.__WEBEXE_CONFIG__ = {
        titleBarColor: options.titleBarColor || '#2d2d2d',
        textColor: options.textColor || '#ffffff',
        borderColor: options.borderColor || '#1a1a1a',
        showNav: options.showNav !== undefined ? options.showNav : true,
        showWindowControls: options.showWindowControls !== undefined ? options.showWindowControls : true,
        forceInternal: options.forceInternal || false,
        customTitle: options.customTitle || 'App'
    };
}
