// mapserver template - this is used to respond to getfeatureinfo requests with a JSON result
[resultset layer=results]
{ "results": [[feature trimlast=","]{"nmtk_id":[nmtk_feature_id]},[/feature]] }
[/resultset]
