define(['jquery',
        'underscore',
        'backbone',
        'js/views/UserView',
        'js/views/JobView',
        'js/views/JobView2',
        'js/views/ToolView',
        'js/views/JobConfig',
        'js/views/DatafileView',
        'js/views/DatafileView2',
        'js/views/CreateJobView'],
        function ($, _, Backbone, UserView, JobView, JobView2, ToolView, 
        		  JobConfigView, DatafileView,
        		  DatafileView2, CreateJobView) {
			var NMTKRouter=Backbone.Router.extend({
				routes: {
					'users': 'ShowUsers',
					'job/*path': 'CreateJob',
					'configure/*jobid': 'ConfigureJob',
					'*other': 'ShowDashboard'
				}
			});
		
			var initialize = function() {
				var nmtk_router=new NMTKRouter;
				var toolView=new ToolView();
				var jobView=new JobView();
				var jobView2=new JobView2();
				var datafileView=new DatafileView();
				var datafileView2=new DatafileView2();
				var createJobView=new CreateJobView();
				var jobConfigView=new JobConfigView();
				toolView.render();
				jobView.render();
				datafileView.render();
				
				var switchtab=function (showtag) {
					tags=['#dashboard','#configurejob','#createjob'];
					for (tag in tags) {
						if (tags[tag] != showtag) {
							$(tags[tag]).hide();
							$(tags[tag] + '-tab').removeClass('active');
						} else {
							$(tags[tag]).show();
							$(tags[tag] + '-tab').addClass('active');
						}
					}
				}
				nmtk_router.on('route:CreateJob', function () {
					switchtab('#createjob');
					// Stop the view updates while we are on another tab
					datafileView.stopped=jobView.stopped=true;
					toolView.stopped=false;
					toolView.render();
					datafileView2.render();
					jobView2.render();
					createJobView.render();
				});
				nmtk_router.on('route:ConfigureJob', function (jobid) {
					switchtab('#configurejob');
					jobConfigView.render(jobid);
				});
				nmtk_router.on('route:ShowDashboard', function (other) {
					switchtab('#dashboard');
					// Start the view updates when we move to the relevant tab
					datafileView.stopped=jobView.stopped=false;
					toolView.stopped=true;
					jobView.render();
					datafileView.render();
				})
				Backbone.history.start();
			};
			
			return {
				initialize: initialize
			};
});