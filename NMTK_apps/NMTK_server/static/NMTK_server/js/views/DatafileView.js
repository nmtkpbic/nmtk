define(['jquery',
        'backbone',
        'underscore',
        'text!templates/datafile/list.html',
        'text!templates/pager.html',
        'jquery.cookie',
        'jquery.fileupload',
        'jquery.iframe-transport'], 
   function ($, Backbone, _,
		   DatafileListTemplate, PagerTemplate) {
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
			    // add the dataTransfer property for use with the native `drop` event
			    // to capture information about files dropped into the browser window
			    _.bindAll(this, 'pager', 'render');
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
			   var datafiles=new Datafiles();
			   // Limit sets the number of items that appear on each page
			   var limit=10;
			   datafiles.fetch({
				   data: $.param({ limit: limit,
					               offset: offset}),
				   success: function (tools) {
				   		var context={'datafiles': datafiles.models,
  								 	 'meta': datafiles.recent_meta,
  								 	 'url': datafiles.url };
				   		var pager=_.template(PagerTemplate, context);	
				   		context['pagertemplate']=pager;
				   		var template=_.template(DatafileListTemplate,
				   								context);
				   		that.$el.html(template);
				   		$('#fileUpload', that.el).fileupload();
					    $('#fileUpload', that.el).fileupload('option', {
					    	   url: datafiles.url,
					    	   paramName: 'file',
		    				   headers: {
					    				  'X-CSRFToken': $.cookie('csrftoken')
					    				 },
		    				   progressall: function (e, data) {
		    				        var progress = parseInt(data.loaded / data.total * 100, 10);
		    				        $('#progress .bar', that.el).css(
		    				            'width',
		    				            progress + '%'
		    				         );
		    				   },
		    				   always: function () { that.render(); }
					    	   
					    });
			   		}
			   
			   })
		}
		});
		return DatafileView;	
});