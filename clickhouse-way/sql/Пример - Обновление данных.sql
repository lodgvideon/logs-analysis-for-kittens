alter table logs_table_v1 update label = multiIf(
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /search'),
                                                    'GET /search',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /about'),
                                                    'GET /about',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post.*[aA]ction1'),
                                                    'POST /post (Action1)',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post.*[aA]ction2'),
                                                    'POST /post (Action2)',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post.*[aA]ction3'),
                                                    'POST /post (Action3)',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), '') || ' ' ||
                                                          request_body, '^POST /post'), 'POST /post',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /profile/'),
                                                    'GET /profile/{user}',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET /product/'),
                                                    'GET /product/{productId}',
                                                    match(request_type || ' ' || path ||
                                                          if(params != '', concat('?', params), ''), '^GET / '),
                                                    'GET / ',
                                                    'other'
                                            )
