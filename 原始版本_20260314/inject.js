(function() {
    if (document.getElementById('webexe-titlebar-host')) return;
    
    var config = window.__WEBEXE_CONFIG__ || {
        titleBarColor: '#2d2d2d',
        textColor: '#ffffff',
        borderColor: '#1a1a1a',
        showNav: true,
        showWindowControls: true,
        forceInternal: false,
        customTitle: 'App'
    };
    
    var globalStyle = document.createElement('style');
    globalStyle.id = 'webexe-global-style';
    globalStyle.textContent = '\
        html, body {\
            overflow-x: hidden !important;\
            overflow-y: auto !important;\
        }\
        ::-webkit-scrollbar {\
            display: none !important;\
            width: 0 !important;\
            height: 0 !important;\
        }\
        * {\
            scrollbar-width: none !important;\
            -ms-overflow-style: none !important;\
        }\
    ';
    document.head.appendChild(globalStyle);
    
    if (!config.showNav && !config.showWindowControls) {
        return;
    }
    
    var host = document.createElement('div');
    host.id = 'webexe-titlebar-host';
    host.style.cssText = "position: fixed; top: 0; left: 0; width: 100%; z-index: 2147483647; pointer-events: none;";
    document.body.appendChild(host);
    
    var shadow = host.attachShadow({ mode: 'open' });
    
    var style = document.createElement('style');
    style.textContent = '\
        * { box-sizing: border-box; user-select: none; }\
        \
        .title-bar {\
            height: 30px;\
            background: ' + config.titleBarColor + ';\
            display: flex;\
            align-items: center;\
            pointer-events: auto;\
            color: ' + config.textColor + ';\
            font-family: system-ui, -apple-system, "Segoe UI", sans-serif;\
            -webkit-app-region: drag;\
        }\
        \
        .btn-group { display: flex; gap: 2px; margin-left: 5px; }\
        .btn {\
            background: ' + config.titleBarColor + ';\
            border: 1px solid ' + config.borderColor + ';\
            color: ' + config.textColor + ';\
            min-width: 30px;\
            height: 22px;\
            cursor: pointer;\
            border-radius: 4px;\
            display: flex;\
            align-items: center;\
            justify-content: center;\
            font-size: 12px;\
            transition: background 0.2s;\
            -webkit-app-region: no-drag;\
        }\
        \
        .btn:hover { \
            background: rgba(255, 255, 255, 0.1); \
        }\
        \
        .window-controls { display: flex; margin-left: auto; }\
        .window-btn {\
            width: 30px;\
            height: 30px;\
            display: flex;\
            align-items: center;\
            justify-content: center;\
            cursor: pointer;\
            transition: background 0.2s;\
            font-size: 14px;\
            border: none;\
            outline: none;\
            background: transparent;\
            padding: 0;\
            margin: 0;\
            -webkit-app-region: no-drag;\
        }\
        \
        .window-btn:hover {\
            background: rgba(255, 255, 255, 0.1);\
        }\
        \
        .window-btn.close:hover {\
            background: #e81123;\
        }\
        \
        .title {\
            font-size: 12px;\
            font-weight: 600;\
            color: ' + config.textColor + ';\
            opacity: 0.7;\
            overflow: hidden;\
            white-space: nowrap;\
            text-overflow: ellipsis;\
            max-width: 300px;\
            margin-left: 10px;\
        }\
        \
        ::-webkit-scrollbar {\
            display: none;\
            width: 0;\
            height: 0;\
        }\
        \
        * {\
            scrollbar-width: none;\
            -ms-overflow-style: none;\
        }\
    ';
    shadow.appendChild(style);
    
    var container = document.createElement('div');
    container.className = 'title-bar';
    
    var leftContent = '';
    var rightContent = '';
    
    if (config.showNav) {
        leftContent = '\
            <div class="btn-group">\
                <button class="btn" id="btn-back" title="\u540e\u9000">\u2b05</button>\
                <button class="btn" id="btn-forward" title="\u524d\u8fdb">\u27a1</button>\
                <button class="btn" id="btn-refresh" title="\u5237\u65b0">\u21bb</button>\
            </div>\
        ';
    }
    
    if (config.showWindowControls) {
        rightContent = '\
            <div class="window-controls">\
                <button class="window-btn" id="btn-minimize" title="\u6700\u5c0f\u5316" onmousedown="event.stopPropagation(); event.preventDefault();">\u2500</button>\
                <button class="window-btn" id="btn-maximize" title="\u6700\u5927\u5316" onmousedown="event.stopPropagation(); event.preventDefault();">\u25a1</button>\
                <button class="window-btn close" id="btn-close" title="\u5173\u95ed" onmousedown="event.stopPropagation(); event.preventDefault();">\u2715</button>\
            </div>\
        ';
    }
    
    container.innerHTML = leftContent + '<div class="title">' + config.customTitle + '</div>' + rightContent;
    
    shadow.appendChild(container);
    
    document.body.style.paddingTop = '30px';
    document.body.style.height = 'calc(100vh - 30px)';
    document.body.style.overflow = 'auto';
    
    var btnBack = shadow.getElementById('btn-back');
    var btnForward = shadow.getElementById('btn-forward');
    var btnRefresh = shadow.getElementById('btn-refresh');
    var btnMinimize = shadow.getElementById('btn-minimize');
    var btnMaximize = shadow.getElementById('btn-maximize');
    var btnClose = shadow.getElementById('btn-close');
    
    if (btnBack) btnBack.onclick = function() { window.history.back(); };
    if (btnForward) btnForward.onclick = function() { window.history.forward(); };
    if (btnRefresh) btnRefresh.onclick = function() { window.location.reload(); };
    if (btnMinimize) btnMinimize.onclick = function() { 
        if (window.pywebview && window.pywebview.api) window.pywebview.api.minimize(); 
    };
    if (btnMaximize) btnMaximize.onclick = function() { 
        if (window.pywebview && window.pywebview.api) window.pywebview.api.destroy(); 
    };
    if (btnClose) btnClose.onclick = function() { 
        if (window.pywebview && window.pywebview.api) window.pywebview.api.destroy(); 
    };
    
    if (config.forceInternal) {
        document.addEventListener('click', function(e) {
            var link = e.target.closest('a');
            if (link && link.href && !link.href.startsWith('javascript:')) {
                if (link.href.includes('#') && link.href.split('#')[0] === window.location.href.split('#')[0]) return;
                e.preventDefault(); 
                e.stopPropagation();
                window.location.href = link.href;
            }
        }, true);
    }
})();
