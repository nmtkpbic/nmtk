define(['jquery',
        'backbone',], 
   function ($, Backbone) {
	var DatafileCollection=Backbone.Collection.extend({
		url: $('#api').data('api') + 'datafile/?format=json',
		
		// Needed for TastyPie support, since we want meta..
		parse: function(response) {
	  	    this.page = response.meta.offset/response.meta.limit+1;
	  	    this.recent_meta = response.meta || {};
	  	    return response.objects || response;
	    },
	});
	return DatafileCollection;
});