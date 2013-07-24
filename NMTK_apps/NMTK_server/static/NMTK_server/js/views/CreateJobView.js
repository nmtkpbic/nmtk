define(['jquery',
        'backbone',
        'underscore',
        'js/models/JobModel',
        'text!templates/job/createjob.html'], 
   function ($, Backbone, _, JobModel,
		     CreateJobTemplate) {		
		
		var CreateJobView = Backbone.View.extend({
			el: $('#createjob_button'),
			initialize: function() {
			    // add the dataTransfer property for use with the native `drop` event
			    // to capture information about files dropped into the browser window
			    _.bindAll(this, 'render', 'createjob');
			},
			events: {
			    'click': 'createjob',
			},
			
			createjob: function (elem) {
				var tool=$('input:checkbox[name="tool_uri"]:checked').val();
				var file=$('input:checkbox[name="datafile_uri"]:checked').val()
				if ((typeof tool === 'undefined') || (typeof file === 'undefined')) {
					alert('Please choose a tool and datafile first');
					return;
				} else {
					var job=new JobModel();
					job.save({data_file: file,
							  tool: tool
							},{
							success: function (job) {
								 Backbone.history.navigate('#/configure/'+job.get("job_id")) 
							}
							});
				}
				
				
			},
			
			render: function () {
			   this.$el.html('Configure Job');
			}
		});
		return CreateJobView;	
});