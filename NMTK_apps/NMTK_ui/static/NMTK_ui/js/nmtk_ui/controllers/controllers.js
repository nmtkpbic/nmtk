/*
 * Chander Ganesan, 2013 (chander@otg-nc.com)
 * Controller loader for NMTK UI components, here is where
 * all the controllers should be referenced so that other
 * NMTK components can load them easily.
 */

define([
  // Standard Libs
  'underscore' // lib/underscore/underscore
  , 'nmtk_ui/controllers/NMTKCtrl' // Application Controller
  , 'nmtk_ui/controllers/SwitchJobCtrl' // Application Controller
  , 'nmtk_ui/controllers/ChangePasswordCtrl' // Controller to handle password changes
  , 'nmtk_ui/controllers/CloneConfigCtrl' // Modal dialog for cloning configuration
  , 'nmtk_ui/controllers/ConfigureCtrl' // Job configuration controller
  , 'nmtk_ui/controllers/CreateJobCtrl' // Controller for creating a new job
  , 'nmtk_ui/controllers/DeleteCtrl' // Ack modal for deleting a job
  , 'nmtk_ui/controllers/DownloadDatafileCtrl' // Modal Controller to download job(s) NOT USED?
  , 'nmtk_ui/controllers/FeedbackCtrl' // Grouse facility controller
  , 'nmtk_ui/controllers/FileInfoUpdateCtrl' // Controller for file information update (modal)
  , 'nmtk_ui/controllers/FilesCtrl' // Controller for file management page
  , 'nmtk_ui/controllers/IntroCtrl' // Main/intro page controller
  , 'nmtk_ui/controllers/JobCtrl' // Controller for Job management page
  , 'nmtk_ui/controllers/ToolExplorerCtrl' // Controller for Tool explorer page
  , 'nmtk_ui/controllers/ViewJobCtrl' // Controller for Viewing Job data (modal)
  , 'nmtk_ui/controllers/ViewDatafileCtrl' // Controller handling the view results page(s)
  , 'nmtk_ui/controllers/LoginCtrl' // Controller handling the user login process
], function ( _, NMTKCtrl, SwitchJobCtrl, 
		ChangePasswordCtrl, CloneConfigCtrl, ConfigureCtrl,
		CreateJobCtrl, DeleteCtrl, DownloadDatafileCtrl, FeedbackCtrl,
		FileInfoUpdateCtrl, FilesCtrl, IntroCtrl, JobCtrl,
		ToolExplorerCtrl, ViewJobCtrl, ViewDatafileCtrl, LoginCtrl
			 ) {
  "use strict";
  var controllers = {
	"NMTKCtrl": NMTKCtrl
	, "SwitchJobCtrl": SwitchJobCtrl
	, "ChangePasswordCtrl": ChangePasswordCtrl
	, "CloneConfigCtrl": CloneConfigCtrl
	, "ConfigureCtrl": ConfigureCtrl
	, "CreateJobCtrl": CreateJobCtrl
	, "DeleteCtrl": DeleteCtrl
	, "DownloadDatafileCtrl": DownloadDatafileCtrl
	, "FeedbackCtrl": FeedbackCtrl
	, "FileInfoUpdateCtrl": FileInfoUpdateCtrl
	, "FilesCtrl": FilesCtrl
	, "IntroCtrl": IntroCtrl
	, "JobCtrl": JobCtrl
	, "ToolExplorerCtrl": ToolExplorerCtrl
	, "ViewJobCtrl": ViewJobCtrl
	, "ViewDatafileCtrl": ViewDatafileCtrl
	, "LoginCtrl": LoginCtrl
  };
  
  var initialize = function(angModule) {
    // Register all the controllers we are using here.
    _.each(controllers,function(controller,name){
      angModule.controller(name, controller);
    })
  };

  return {
    initialize: initialize
  };
});