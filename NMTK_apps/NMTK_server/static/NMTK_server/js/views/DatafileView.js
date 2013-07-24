define(['jquery',
        'backbone',
        'underscore',
        'js/models/DatafileModel',
        'js/collections/DatafileCollection',
        'text!templates/datafile/list.html',
        'text!templates/pager.html',
        'jquery.cookie',
        'jquery.fileupload',
        'jquery.iframe-transport'], 
   function ($, Backbone, _, DatafileModel, DatafileCollection,
		   DatafileListTemplate, PagerTemplate) {			
		var DatafileView = Backbone.View.extend({
			el: $('#datafiles'),
			offset: 0,
			limit: 5,
			stopped: false,
			initialize: function() {
			    // add the dataTransfer property for use with the native `drop` event
			    // to capture information about files dropped into the browser window
			    _.bindAll(this, 'pager', 'render', 'edit','destroy');
			},
			events: {
			    'click a.pager': 'pager',
			    'click a.refresh': 'render',
			    'click a.remove': 'destroy',
			    'click a.edit': 'edit'
			},
			pager: function(item) {
				var offset=$(item.currentTarget).data('offset');
			    this.render(offset);
			    return false;
			},
			
			destroy: function(item) {
				var id=$(item.currentTarget).data('pk');
				var model=new DatafileModel({'id': id});
				var that=this;
				model.destroy({
					success: function(model, response) {
								that.render();
							}
				});
			},

			edit: function(item) {
				var id=$(item.currentTarget).data('pk');
				console.log('Edit ' + id)
			},
			
			render: function (offset) {
			   if (this.stopped) { return; }
			   if (typeof offset !== 'undefined') {
				   this.offset=offset;
			   } 
			   var that=this;
			   var datafiles=new DatafileCollection();
			   datafiles.fetch({
				   data: $.param({ limit: this.limit,
					               offset: this.offset}),
				   success: function (datafiles) {
				   		if ((datafiles.models.length == 0) &&
				   			(datafiles.recent_meta.total_count > 0) &&
				   			(datafiles.offset != 0)) {
				   			that.offset-=that.limit;
				   			_.delay(that.render, 1);
				   			return;
				   		}
				   		var context={'datafiles': datafiles.models,
  								 	 'meta': datafiles.recent_meta,
  								 	 'url': datafiles.url };
				   		var pager=_.template(PagerTemplate, context);	
				   		context['pagertemplate']=pager;
				   		var template=_.template(DatafileListTemplate,
				   								context);
				   		that.$el.html(template);
				   		// Update every 2 seconds until the files processing
				   		// are complete, then switch to every 60s to catch
				   		// uploads that might have happened in other windows.
				   		_.delay(that.render, datafiles.recent_meta.refresh_interval);
				   		$('#fileUpload', that.el).fileupload();
					    $('#fileUpload', that.el).fileupload('option', {
					    	   url: datafiles.url,
					    	   paramName: 'file',
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