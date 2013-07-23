define(['jquery',
        'backbone',
        'underscore',
        'text!templates/job/list.html',
        'text!templates/pager.html'], 
   function ($, Backbone, _, JobListTemplate, PagerTemplate) {
		var Jobs=Backbone.Collection.extend({
			url: $('#api').data('api') + 'job/?format=json',
			
			// Needed for TastyPie support, since we want meta..
			parse: function(response) {
		  	    this.page = response.meta.offset/response.meta.limit+1;
		  	    this.recent_meta = response.meta || {};
		  	    return response.objects || response;
		    },
		});
		
		var JobView = Backbone.View.extend({
			el: $('#jobs'),
			initialize: function() {
			    _.bindAll(this, 'pager');
			},
			events: {
			    'click a.pager': 'pager',
			    'click a.refresh': 'render',
			},
			pager: function(item) {
				var offset=$(item.target).data('offset');
			    this.render(offset);
			    return false;
			},
			 
			render: function (offset) {
			   if (typeof offset === 'undefined') {
				   offset=0;
			   }
			   var that=this;
			   var jobs=new Jobs();
			   // Limit sets the number of items that appear on each page
			   var limit=2;
			   jobs.fetch({
				   data: $.param({ limit: limit,
					               offset: offset}),
				   success: function (tools) {
				   		var context={'jobs': jobs.models,
  								 	 'meta': jobs.recent_meta};
				   		var pager=_.template(PagerTemplate, context);	
				   		context['pagertemplate']=pager;
				   		var template=_.template(JobListTemplate,
				   								context);
				   		that.$el.html(template);
			   		}
			   })
		}
		});
		return JobView;	
});