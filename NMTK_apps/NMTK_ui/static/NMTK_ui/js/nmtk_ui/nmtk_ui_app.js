define(['jquery'
        , 'angular'
        , 'underscore'
        , 'nmtk_ui/controllers/controllers'
        , 'text!deleteModalTemplate'
        , 'text!resultsTemplate'
        , 'text!jobTemplate'
        , 'text!filesTemplate'
        , 'text!configureTemplate'
        , 'text!explorerTemplate'
        , 'text!introTemplate'
        , 'leaflet'
        , 'angular-leaflet'
        , 'restangular'
        , 'ng-grid'
        , 'angular-bootstrap'
        ],
		function ($, angular, _, controllers, deleteModalTemplate,
				  resultsTemplate, jobTemplate, filesTemplate, configureTemplate,
				  explorerTemplate, introTemplate, L) {
			"use strict";
			var initialize=function () {
				$.ajaxSetup({
				    headers: {'X-CSRFToken': CONFIG.csrftoken }
				});
				$.event.props.push('dataTransfer');
				
				/*  
				 * Initialize our application
				 */
				
				var nmtk_app=angular.module('nmtk', ['ui.bootstrap', 'restangular', 'ngGrid', 
				                                     'leaflet-directive']).
				   config(['RestangularProvider', 
					function(RestangularProvider) {
					  var api_path=CONFIG.api_path;
					  // Otherwise IE8 is broken...
					  if (/\//.test(CONFIG.api_path)) {
						  api_path=CONFIG.api_path.substring(0, CONFIG.api_path.length-1);
					  }
					  RestangularProvider.setBaseUrl(api_path);
					  RestangularProvider.setDefaultHeaders({'X-CSRFToken': CONFIG.csrftoken });
					  RestangularProvider.setDefaultRequestParams({format: 'json',
						                                           limit: 9999});
					  // If the trailing slash isn't there, we redirect to the trailing slash url
					  // - but that breaks things since post requests
					  // get cancelled.  Ensure there's always a trailing slash...
					  RestangularProvider.setRequestSuffix('/');
					  RestangularProvider.setResponseExtractor(function(data, operation, what, url, response) {
					        var newResponse;
					        if (operation === "getList") {
					            newResponse = data.objects;
					            newResponse.metadata = data.meta;
					        } else if (operation == 'post') {
					        	var base_url=(location.protocol + '//' + location.hostname)
					        	var response_uri=response.headers().location;
					        	newResponse={'resource_uri': response_uri.replace(base_url,'')};
							} else {
					            newResponse = data;
					        }
					        return newResponse;
					  });
			        }]).config(['$routeProvider', function ($routeProvider) {
					  $routeProvider.
					  	  when('/view_results/:job_id/', {controller: 'ViewDatafileCtrl',  
					  		  							  template: resultsTemplate}).
					  	  when('/view_file/:datafile_id/', {controller: 'ViewDatafileCtrl',  
					  		  							  	template: resultsTemplate}).
					  	  when('/job', {controller: 'JobCtrl',  
							  			template: jobTemplate}).
					      when('/files', {controller: 'FilesCtrl',
					    	  			  template: filesTemplate}).
					      when('/job/:jobid/', {controller:'ConfigureCtrl',
					    	  				    template: configureTemplate}).
					      when('/tool-explorer/:toolid', {controller:'ToolExplorerCtrl',
					    	    	  			  		  template: explorerTemplate}).
					      when('/', {controller:'IntroCtrl', 
					    		     template: introTemplate}).
					      otherwise({redirectTo:'/'});
			        }]).filter('page', [function() {
						  return function(input, metadata) {
							  if (metadata) {
							     var total = parseInt(metadata.total_count);
							     var step= parseInt(metadata.limit);
							     for (var i=0; i<total; i+=step)
							       input.push(i);
							  } 
							  return input;
						  }
					}]).directive('stopEvent', [function () {
						// Usage is (in a tag) stop-event='click' (or the event you wish to 
						// stop from propagating)  This prevents events from propagating...
				        return {
				            restrict: 'A',
				            link: function (scope, element, attr) {
				                element.bind(attr.stopEvent, function (e) {
				                    e.stopPropagation();
				                });
				            }
				        }
					}]);
				
		        controllers.initialize(nmtk_app);
	        	angular.bootstrap(window.document,['nmtk']);			
	        }
			return { initialize: initialize };
});
