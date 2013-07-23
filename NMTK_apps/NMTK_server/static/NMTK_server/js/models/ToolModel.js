define(['jquery',
        'backbone',], 
   function ($, Backbone) {
	var ToolModel=Backbone.Model.extend({
			url: function() {
				var origUrl = Backbone.Model.prototype.url.call(this);
	        	return origUrl + (origUrl.charAt(origUrl.length - 1) == '/' ? '' : '/') + '?format=json';
	    	},
			urlRoot: $('#api').data('api') +'tool/'
		});
	return ToolModel;
});