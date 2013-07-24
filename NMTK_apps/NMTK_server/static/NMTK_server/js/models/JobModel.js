define(['jquery',
        'backbone',], 
   function ($, Backbone) {
	var JobModel=Backbone.Model.extend({
			idAttribute : 'job_id',
			url: function() {
				var origUrl = Backbone.Model.prototype.url.call(this);
	        	return origUrl + (origUrl.charAt(origUrl.length - 1) == '/' ? '' : '/') + '?format=json';
	    	},
			urlRoot: $('#api').data('api') +'job/'
		});
	return JobModel;
});