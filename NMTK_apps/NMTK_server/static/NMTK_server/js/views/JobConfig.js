define(['jquery',
        'backbone',
        'underscore',
        'js/models/JobModel',
        'text!templates/job/configuration.html',
        'text!templates/job/configuration_complete.html',
        'backbone.syphon',
        'json2'], 
   function ($, Backbone, _, JobModel, JobConfigTemplate, JobConfigCompleteTemplate) {
		var JobConfigView = Backbone.View.extend({
			el: $('#job-configuration'),
			initialize: function() {
				_.bindAll(this, 'render', 'validate');
			},
			events: {
			    'click #configurejob_button': 'validate'
			},
			
			validate: function () {
				var that=this;
				var data=Backbone.Syphon.serialize($('form', this.el)[0]);
				this.job.save({"config": JSON.stringify(data, null, 2)},
						{
						success: function (job) {
							JobConfigCompleteTemplate
							var context={}
							var template=_.template(JobConfigCompleteTemplate, 
	   				                				context);
							$('#configurejob-tab').data('hide', true);
							that.$el.html(template);
						},
						error: function (job, xhr, options) {
							errors=JSON.parse(xhr.responseText);
							console.log(errors);
						}
				})
			},
			 
			render: function (jobid) {
			   var that=this;
			   var job=new JobModel({'job_id': jobid });
			   var url="#/configure/"+jobid;
			   $('#configurejob-tab').show();
			   $('#configurejob-tab').data('hide', false);
			   var $tab=$('#configurejob-tab a');
			   if ((url != $tab.attr("href")) && (typeof jobid !== 'undefined')) {
				   $tab.attr("href", url);
				   job.fetch({
					   success: function(job) {
					   		// Store the job to save time later.
					   		that.job=job;
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