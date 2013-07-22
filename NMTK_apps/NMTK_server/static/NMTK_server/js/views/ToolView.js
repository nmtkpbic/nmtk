define(['jquery',
        'backbone',
        'underscore',
        'text!templates/tool/list.html',
        'text!templates/pager.html'], 
   function ($, Backbone, _, ToolListTemplate, PagerTemplate) {
		var Tools=Backbone.Collection.extend({
			url: $('#api').data('api') + 'tool/?format=json',
			
			// Needed for TastyPie support, since we want meta..
			parse: function(response) {
		  	    this.page = response.meta.offset/response.meta.limit+1;
		  	    this.recent_meta = response.meta || {};
		  	    return response.objects || response;
		    },
		});
		
		var ToolView = Backbone.View.extend({
			el: $('#tools'),
			initialize: function() {
			    _.bindAll(this, 'pager');
//			    _.bindAll(this, 'toolrefresh');
//			    this.collection.bind('refresh', this.render);
			},
			events: {
			    'click a.toolpager': 'pager',
			    'click a.toolrefresh': 'render',
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
			   var tools=new Tools();
			   // Limit sets the number of items that appear on each page
			   var limit=2;
			   tools.fetch({
				   data: $.param({ limit: limit,
					               offset: offset}),
				   success: function (tools) {
				   		var context={'tools': tools.models,
  								 	 'pagerclass': 'toolpager',
  								 	 'meta': tools.recent_meta};
				   		var pager=_.template(PagerTemplate, context);	
				   		context['pagertemplate']=pager;
				   		var template=_.template(ToolListTemplate,
				   								context);
				   		that.$el.html(template);
			   		}
			   })
		}
		});
		return ToolView;	
});