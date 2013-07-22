require.config({
		
		// Note: The line below is only for development, and should be removed
		// before deployment.
		baseUrl: ""
		urlArgs: "bust=" +  (new Date()).getTime(),
		paths: {
			"jquery": "libs/jquery-1.9.1.min",
			"jquery.bootstrap": "libs/bootstrap.min",
			"jquery.ui": "libs/jquery-ui-1.10.0.custom.min",
			"jquery.private": "libs/jquery-private",
			"backbone": "libs/backbone.min",
			"underscore": "libs/underscore.min",
			"Application": "Application",
			"NMTK": "NMTK",
			"text": "libs/text"
		},
		shim: {
			'backbone': { deps: ['underscore','jquery'],
			              exports: 'Backbone' },
			'underscore': { exports: '_' },
			'jquery.bootstrap': { deps: ['jquery'] },
			'jquery.ui': { deps: ['jquery'] },
		}
});

require(['Application','NMTK']); 