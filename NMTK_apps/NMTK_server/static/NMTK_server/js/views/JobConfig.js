define(['jquery',
        'backbone',
        'underscore',
        'js/models/JobModel',
        'text!templates/job/configuration.html',
        'backbone.syphon',
        'json2'], 
   function ($, Backbone, _, JobModel, JobConfigTemplate) {
		var JobConfigView = Backbone.View.extend({
			el: $('#job-configuration'),
			initialize: function() {
				_.bindAll(this, 'render', 'validate');
			},
			events: {
			    'click #configurejob_button': 'validate'
			},
			
			validate: function () {
				var data=Backbone.Syphon.serialize($('form', this.el)[0]);
				this.job.set("config", JSON.stringify(data, null, 2));
				this.job.save();
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