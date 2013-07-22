define(['jquery',
        'underscore',
        'backbone',
        'js/views/UserView',
        'js/views/JobView',
        'js/views/ToolView',
        'js/views/DataFileView'],
        function ($, _, Backbone, UserView, JobView, ToolView, DatafileView) {
			var NMTKRouter=Backbone.Router.extend({
				routes: {
					'/users': 'ShowUsers',
					'/jobs': 'ShowJobs',
					'/tools': 'ShowTools',
					'/files': 'ShowFiles',
					'*actions': 'defaultAction'
				}
			});
		
			var initialize = function() {
				var nmtk_router=new NMTKRouter;
				nmtk_router.on('route:ShowUsers', function () {
					var userView=new UserView();
					userView.render();
				});
				nmtk_router.on('route:ShowJobs', function () {
					var jobView=new JobView();
					jobView.render();
				});
				nmtk_router.on('route:ShowTools', function () {
					var toolView=new ToolView();
					toolView.render();
				});
				nmtk_router.on('route:ShowFiles', function () {
					var datafileView=new DatafileView();
					datafileView.render();
				});
				nmtk_router.on('defaultAction', function (actions) {
					console.log('No route:', actions)
				});
				var toolView=new ToolView();
				toolView.render();
				var jobView=new JobView();
				jobView.render();
				Backbone.history.start();
				var datafileView=new DatafileView();
				datafileView.render();
			};
			
			return {
				initialize: initialize
			};
});