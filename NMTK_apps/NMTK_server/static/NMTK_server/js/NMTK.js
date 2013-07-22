
define(['jquery',
        'underscore', 
        'backbone', 
        'js/router'], 
		function ($, _, Backbone, Router){
			var initialize = function () {
				Router.initialize();
			}
			return {
				initialize: initialize
			};

		});