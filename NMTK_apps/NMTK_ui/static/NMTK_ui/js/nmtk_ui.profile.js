({
    mainConfigFile: "./nmtk_ui.js", 
    name: "nmtk_ui_app",
    out: "nmtk_ui_app.min.js",
    paths: {
    	requireLib: "lib/require",
    },
	include: ["requireLib", "json2","html5shiv", "jquery.ui.widget",
	          "jquery-fileupload", "jquery-iframe-transport",
	          "browserdetect", "respond"]
})
