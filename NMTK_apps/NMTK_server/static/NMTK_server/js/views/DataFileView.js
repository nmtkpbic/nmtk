define(['jquery',
        'backbone',
        'underscore',
        'text!templates/datafile/list.html',
        'text!templates/pager.html'], 
   function ($, Backbone, _, DatafileListTemplate, PagerTemplate) {
		var Datafiles=Backbone.Collection.extend({
			url: $('#api').data('api') + 'datafile/?format=json',
			
			// Needed for TastyPie support, since we want meta..
			parse: function(response) {
		  	    this.page = response.meta.offset/response.meta.limit+1;
		  	    this.recent_meta = response.meta || {};
		  	    return response.objects || response;
		    },
		});
		
		var DatafileView = Backbone.View.extend({
			el: $('#datafiles'),
			initialize: function() {
			    _.bindAll(this, 'pager');
//			    _.bindAll(this, 'toolrefresh');
//			    this.collection.bind('refresh', this.render);
			},
			events: {
			    'click a.datafilepager': 'pager',
			    'click a.datafilerefresh': 'render',
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
			   var datafiles=new Datafiles();
			   // Limit sets the number of items that appear on each page
			   var limit=2;
			   datafiles.fetch({
				   data: $.param({ limit: limit,
					               offset: offset}),
				   success: function (tools) {
				   		var context={'datafiles': jobs.models,
  								 	 'pagerclass': 'datafilepager',
  								 	 'meta': datafiles.recent_meta};
				   		var pager=_.template(PagerTemplate, context);	
				   		context['pagertemplate']=pager;
				   		var template=_.template(DatafileListTemplate,
				   								context);
				   		that.$el.html(template);
			   		}
			   })
		}
		});
		return DatafileView;	
});