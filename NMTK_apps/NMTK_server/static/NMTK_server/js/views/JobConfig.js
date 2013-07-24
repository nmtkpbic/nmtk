define(['jquery',
        'backbone',
        'underscore',
        'js/models/JobModel',
        'text!templates/job/configuration.html'], 
   function ($, Backbone, _, JobModel, JobConfigTemplate) {
		var JobConfigView = Backbone.View.extend({
			el: $('#job-configuration'),
			initialize: function() {
				_.bindAll(this, 'render');
			},

			edit: function(item) {
				var id=$(item.currentTarget).data('pk');
				console.log(id);
				job=new JobModel({'job_id': id });
				job.fetch({
					success: function (job) {
						alert(job.toJSON());
					}
				});
			},
			 
			render: function (jobid) {
			   var that=this;
			   var job=new JobModel({'job_id': jobid });
			   var url="#/configure/"+jobid;
			   $('#configurejob-tab').show();
			   var $tab=$('#configurejob-tab a');
			   if ((url != $tab.attr("href")) && (typeof jobid !== 'undefined')) {
				   $tab.attr("href", url);
				   job.fetch({
					   success: function(job) {
					   		var context={'job': job}
					   		var template=_.template(JobConfigTemplate, 
					   				                context);
					   		that.$el.html(template);
				   	   }
				   });
			   }
			}
		});
		return JobConfigView;	
});