require.config({
		
		// Note: The line below is only for development, and should be removed
		// before deployment.
		urlArgs: "bust=" +  (new Date()).getTime(),
		paths: {
			"jquery": "libs/jquery-1.9.1.min",
			"jquery.bootstrap": "libs/bootstrap.min",
			"jquery.ui": "libs/jquery-ui-1.10.0.custom.min",
			"jquery.private": "libs/jquery-private",
			"backbone": "libs/backbone.min",
			"NMTK": "NMTK"
		},
		map: {
			'*': { 'jquery': 'libs/jquery-private'},
			'jquery.private': {'jquery': 'jquery'}
		}
});

require(['Application', 'NMTK']); 