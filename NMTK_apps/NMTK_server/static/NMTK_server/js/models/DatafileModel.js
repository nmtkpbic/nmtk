define(['jquery',
        'backbone',], 
   function ($, Backbone) {
	var DatafileModel=Backbone.Model.extend({
			url: function() {
				var origUrl = Backbone.Model.prototype.url.call(this);
	        	return origUrl + (origUrl.charAt(origUrl.length - 1) == '/' ? '' : '/') + '?format=json';
	    	},
			urlRoot: $('#api').data('api') +'datafile/'
		});
	return DatafileModel;
});