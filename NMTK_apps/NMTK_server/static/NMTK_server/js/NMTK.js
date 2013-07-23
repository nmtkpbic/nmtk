
define(['jquery',
        'underscore', 
        'backbone', 
        'js/router',
        'jquery.cookie'], 
		function ($, _, Backbone, Router){
			var initialize = function () {
				$.ajaxSetup({
					    headers: {'X-CSRFToken': $.cookie('csrftoken') }
					  });
				Router.initialize();
			}
			return {
				initialize: initialize
			};

		});