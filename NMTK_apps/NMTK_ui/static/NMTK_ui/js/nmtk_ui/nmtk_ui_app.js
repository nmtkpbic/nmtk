/**
 * @license Non-Motorized Toolkit
 * Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
 * Developed under Federal Highway Administration (FHWA) Contracts:
 * DTFH61-12-P-00147 and DTFH61-14-P-00108
 * 
 * Redistribution and use in source and binary forms, with or without modification, 
 * are permitted provided that the following conditions are met:
 *     * Redistributions of source code must retain the above copyright notice, 
 *       this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright 
 *       notice, this list of conditions and the following disclaimer 
 *       in the documentation and/or other materials provided with the distribution.
 *     * Neither the name of the Open Technology Group, the name of the 
 *       Federal Highway Administration (FHWA), nor the names of any 
 *       other contributors may be used to endorse or promote products 
 *       derived from this software without specific prior written permission.
 *       
 *       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
 *       "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
 *       LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
 *       FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
 *       Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 *       SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
 *       LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
 *       USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
 *       AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 *       OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
 *       OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF 
 *       SUCH DAMAGE.
 */
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
        , 'angular-elastic'
        , 'restangular'
        , 'ng-grid'
        , 'angular-bootstrap'
        , 'bootstrap-slider'
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
				                                     'leaflet-directive', 'monospaced.elastic']).
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
			  	  	  	  when('/view_data/:id', {controller: 'ViewDatafileCtrl',  
			  	  	  		  					  template: resultsTemplate}).
						  when('/view_results/:id', {controller: 'ViewDatafileCtrl',  
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
					}]).directive('dynamicName',['$compile','$parse', function($compile, $parse) {
						  return {
							    restrict: 'A',
							    terminal: true,
							    priority: 100000,
							    link: function(scope, elem) {
							      var name = $parse(elem.attr('dynamic-name'))(scope);
							      elem.removeAttr('dynamic-name');
							      elem.attr('name', name);
							      $compile(elem)(scope);
							    }
							  };
					}]).directive("keepScrollPos", ['$route','$window',
					                                '$timeout','$location','$anchorScroll',
					                                function($route, $window, $timeout, $location, $anchorScroll) {

					    // cache scroll position of each route's templateUrl
					    var scrollPosCache = {};

					    // compile function
					    return function(scope, element, attrs) {

					        scope.$on('$routeChangeStart', function() {
					            // store scroll position for the current view
					            if ($route.current) {
					                scrollPosCache[$route.current.loadedTemplateUrl] = [ $window.pageXOffset, $window.pageYOffset ];
					            }
					        });

					        scope.$on('$routeChangeSuccess', function() {
					            // if hash is specified explicitly, it trumps previously stored scroll position
					            if ($location.hash()) {
					                $anchorScroll();

					            // else get previous scroll position; if none, scroll to the top of the page
					            } else {
					                var prevScrollPos = scrollPosCache[$route.current.loadedTemplateUrl] || [ 0, 0 ];
					                $timeout(function() {
					                    $window.scrollTo(prevScrollPos[0], prevScrollPos[1]);
					                }, 0);
					            }
					        });
					    }
					}]);
				
		        controllers.initialize(nmtk_app);
	        	angular.bootstrap(window.document,['nmtk']);			
	        }
			return { initialize: initialize };
});
