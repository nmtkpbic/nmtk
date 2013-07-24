define(['jquery',
        'backbone',
        'underscore',
        'js/models/JobModel',
        'js/collections/JobsCollection',
        'text!templates/job/list.html',
        'text!templates/pager.html'], 
   function ($, Backbone, _, JobModel, JobsCollection,
		     JobListTemplate, PagerTemplate) {
		var JobView = Backbone.View.extend({
			el: $('#jobs'),
			offset: 0,
			limit: 5,
			stopped: false,
			initialize: function() {
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
				var model=new JobModel({'id': id});
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
			   var jobs=new JobsCollection();
			   jobs.fetch({
				   data: $.param({ limit: this.limit,
					   // Get those jobs which are not unconfigured.
					   			   status__in: 'TF,C,A,F',
					               offset: this.offset}),
				   success: function (jobs) {
				   		if ((jobs.models.length == 0) &&
				   			(jobs.recent_meta.total_count > 0) &&
				   			(jobs.offset != 0)) {
				   			that.offset-=that.limit;
				   			_.delay(that.render, 1);
				   			return;
				   		}
				   		var context={'jobs': jobs.models,
  								 	 'meta': jobs.recent_meta};
				   		var pager=_.template(PagerTemplate, context);	
				   		context['pagertemplate']=pager;
				   		var template=_.template(JobListTemplate,
				   								context);
				   		that.$el.html(template);
				   		// Update every 30s to get any jobs that were completed
				   		_.delay(that.render, jobs.recent_meta.refresh_interval);
			   		}
			   		
			   })
		}
		});
		return JobView;	
});