define(['jquery',
        'backbone',
        'underscore',
        'js/models/ToolModel',
        'text!templates/tool/list.html',
        'text!templates/pager.html'], 
   function ($, Backbone, _, ToolModel, ToolListTemplate, PagerTemplate) {
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
			el: $('#tools_select'),
			limit: 5,
			stopped: false,
			offset: 0,
			initialize: function() {
			    _.bindAll(this, 'pager', 'render', 'checkbox');
			},
			events: {
				'click input:checkbox[name="tool_uri"]': 'checkbox',
			    'click a.pager': 'pager',
			    'click a.refresh': 'render',
			},
			
			checkbox: function (elem) {
				// Ensure only one checkbox is checked at a time.
				var $elem=$(elem.currentTarget);
			    if ($elem.is(":checked")) {
			        var group = "input:checkbox[name='" + $elem.attr("name") + "']";
			        $(group).prop("checked", false);
			        $elem.prop("checked", true);
			    } else {
			        $elem.prop("checked", false);
			    }
			},
			
			pager: function(item) {
				var offset=$(item.currentTarget).data('offset');
			    this.render(offset);
			    return false;
			},
			 
			render: function (offset) {
			   if (this.stopped) { return; }

			   if (typeof offset !== 'undefined') {
				   this.offset=offset;
			   }
			   var that=this;
			   var tools=new Tools();
			   // Limit sets the number of items that appear on each page
			   tools.fetch({
				   data: $.param({ limit: that.limit,
					               offset: that.offset}),
				   success: function (tools) {
				   		var context={'tools': tools.models,
  								 	 'meta': tools.recent_meta};
				   		var pager=_.template(PagerTemplate, context);	
				   		context['pagertemplate']=pager;
				   		var template=_.template(ToolListTemplate,
				   								context);
				   		that.$el.html(template);
				   		// Update every 60s to get any new tools that were
				   		// added.
//				   		_.delay(that.render, tools.recent_meta.refresh_interval);
			   		}
			   })
		}
		});
		return ToolView;	
});