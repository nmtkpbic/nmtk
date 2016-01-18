/**
 * @license Nonmotorized Toolkit
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
        , 'angular-cookies'
        , 'angular-bootstrap'
        , 'bootstrap-slider'
        ],
		function ($, angular, _, controllers, deleteModalTemplate,
				  resultsTemplate, jobTemplate, filesTemplate, configureTemplate,
				  explorerTemplate, introTemplate, L) {
			"use strict";
			var initialize=function () {
//				$.ajaxSetup({
//				    headers: {'X-CSRFToken': CONFIG.csrftoken }
//				});
				$.event.props.push('dataTransfer');
				
				/*  
				 * Initialize our application
				 */
				
				var nmtk_app=angular.module('nmtk', ['ui.bootstrap', 'restangular', 'ngGrid', 'ngCookies',
				                                     'leaflet-directive', 'monospaced.elastic']).
				   config(['RestangularProvider', 
					function(RestangularProvider) {
					  var api_path=CONFIG.api_path;
					  // Otherwise IE8 is broken...
					  if (/\//.test(CONFIG.api_path)) {
						  api_path=CONFIG.api_path.substring(0, CONFIG.api_path.length-1);
					  }
					  RestangularProvider.setBaseUrl(api_path);
//					  RestangularProvider.setDefaultHeaders({'X-CSRFToken': CONFIG.csrftoken });
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
					}]).filter('range', [function() {
						  return function(input, min, max, step) {
							    min = parseInt(min); //Make string input int
							    max = parseInt(max);
							    for (var i=min; i<=max; i+=step)
							      input.push(i);
							    return input;
							  };
					}]).filter('addUsageClass', ['$log', function($log) {
					  return function(curr_property, namespace, field, scope) {
						    var i=-1;
						    /*
						     * The value for options is numeric starting at 0
						     * based on the field position in the list of available
						     * fields, so we need to figure out what the position
						     * is for this one.  Look through until we find a 
						     * item whose field name (value) matches the currently
						     * selected property.
						     */
						    _.find(scope.file_fields[namespace],function(item, index) {
						    	i += 1;
						        return (item.value === curr_property) 
						    });
						    /*
						     * Count up the number of times a field is used from
						     * the current property.
						     */
						    var useCount=scope.fieldUseCount(namespace, curr_property);
						    /*
						     * Construct a jQuery query to selectively get just this
						     * option from the select list for this particular field.
						     * Note: The fields are (dynamically) named "namespace:field"
						     */
						    var elem = angular.element("select[name='"+ namespace + ":" + field  +"'] > option[value='" + i + "']");
						  
						    /*
						     * Apply classes to the option based on the usage count, allowing
						     * us to style these option values differently based on CSS style 
						     * rules.
						     */
						    if (useCount == 1) {
						      elem.addClass('used');
						      elem.removeClass('duplicate');
						    } else if (useCount > 1) {
						      elem.addClass('duplicate');
						      elem.removeClass('used');
						    } else {
						    	elem.removeClass('used');
						    	elem.removeClass('duplicate');
						    }
						    return curr_property;
						  }
					}]).service('preferences', ['Restangular',
					                            function (Restangular) {
						var self=this;
						var default_config = {'divs': [],
											  'ramp': {'ramp_id': 0,
												  	   'reverse': 'false'}
											  };
						var config=angular.copy(default_config);
						this.login=_.debounce(function() {
							Restangular.all('preference').getList().then(function (response) {
								if (response.length) {
									self.preferences=response[0]
				            		config=JSON.parse(self.preferences.config);
									/* 
									 * If the default config has keys that the
									 * user config doesn't have, then update the
									 * user config.
									 */
									_.each(default_config, function (value, key) {
										if (_.isUndefined(config[key])) {
											config[key]=angular.copy(value);
										};
									});
				            	} else {
				            		self.preferences=Restangular.all('preference');
				            	}
							}, function () {
								self.logout();
							});
						}, 200);
					    this.logout = function () {
					    	/*
							 * If the user is not logged in then we give them 
							 * empty preference data.
							 */
					    	config = angular.copy(default_config);
					    	self.preferences=undefined
					    };
						this.save = function () {
							if (self.preferences) {
								self.preferences.config=JSON.stringify(config);
								if (_.isUndefined(self.preferences.resource_uri)) {
									self.preferences.post();
									self.login();
								} else {
									self.preferences.put();
								}
							}
						};
						this.toggleDiv=function(div) {
							if (_.isUndefined(config.divs)) {
								config.divs=[];
							}
							if (_.indexOf(config.divs, div) > -1) {
								config.divs=_.without(config.divs, div);
							} else {
								config.divs.push(div);
							}
							self.save();
						};
						this.isDivEnabled=function(div) {
							return _.indexOf(config.divs, div) == -1;
						}
						this.getRampSettings =function () {
							return config.ramp;
						}
						this.setRampSettings =function (setting) {
							config.ramp=setting;
							self.save();
						}
						this.setOpacity = function (opacity) {
							config.opacity=opacity;
							self.save();
						}
						this.getOpacity = function () {
							if (config.opacity) {
								return config.opacity;
							} else {
								return .7;
							}
						}
						
					}]);
				
		        controllers.initialize(nmtk_app);
	        	angular.bootstrap(window.document,['nmtk']);			
	        }
			return { initialize: initialize };
});
