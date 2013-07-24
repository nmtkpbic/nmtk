define(['jquery',
        'backbone',
        'underscore',
        'js/models/DatafileModel',
        'js/collections/DatafileCollection',
        'text!templates/datafile/list_select.html',
        'text!templates/pager.html',
        'jquery.cookie',
        'jquery.fileupload',
        'jquery.iframe-transport'], 
   function ($, Backbone, _,DatafileModel,DatafileCollection,
		   DatafileListTemplate, PagerTemplate) {		
		var DatafileView = Backbone.View.extend({
			el: $('#datafiles_select'),
			offset: 0,
			limit: 5,
			stopped: false,
			initialize: function() {
			    // add the dataTransfer property for use with the native `drop` event
			    // to capture information about files dropped into the browser window
			    _.bindAll(this, 'pager', 'render', 'checkbox');
			},
			events: {
				'click input:checkbox[name="datafile_uri"]': 'checkbox',
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
			   var datafiles=new DatafileCollection();
			   datafiles.fetch({
				   data: $.param({ limit: this.limit,
					               status: 3,
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
			   		}
			   
			   })
		}
		});
		return DatafileView;	
});