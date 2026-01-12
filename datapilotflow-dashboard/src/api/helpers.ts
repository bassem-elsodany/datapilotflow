import {
  QueryClient,
  UndefinedInitialDataOptions,
  useMutation,
  UseMutationOptions,
  useQuery,
  useQueryClient,
  UseQueryResult,
} from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { useState } from 'react';
import { z, ZodError } from 'zod';
import { client } from './axios';
import { logger } from '@/services/logger';

interface EnhancedMutationParams<
  TData = unknown,
  TError = Error,
  TVariables = void,
  TContext = unknown,
> extends Omit<
  UseMutationOptions<TData, TError, TVariables, TContext>,
  'mutationFn' | 'onSuccess' | 'onError' | 'onSettled'
> {
  onSuccess?: (
    data: TData,
    variables: TVariables,
    context: TContext,
    queryClient: QueryClient
  ) => unknown;
  onError?: (
    error: TError,
    variables: TVariables,
    context: TContext | undefined,
    queryClient: QueryClient
  ) => unknown;
  onSettled?: (
    data: TData | undefined,
    error: TError | null,
    variables: TVariables,
    context: TContext | undefined,
    queryClient: QueryClient
  ) => unknown;
}

/**
 * Create a URL with query parameters and route parameters
 *
 * @param base - The base URL with route parameters
 * @param queryParams - The query parameters
 * @param routeParams - The route parameters
 * @returns The URL with query parameters
 * @example
 * createUrl('/api/users/:id', { page: 1 }, { id: 1 });
 * // => '/api/users/1?page=1'
 */
function createUrl(
  base: string,
  queryParams?: Record<string, string | number | undefined>,
  routeParams?: Record<string, string | number | undefined>
) {
  const url = Object.entries(routeParams ?? {}).reduce(
    (acc, [key, value]) => acc.replaceAll(`:${key}`, String(value)),
    base
  );

  if (!queryParams) {
    return url;
  }

  const query = new URLSearchParams();

  Object.entries(queryParams).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    query.append(key, String(value));
  });

  return `${url}?${query.toString()}`;
}

type QueryKey = [string] | [string, Record<string, string | number | undefined>];

function getQueryKey(
  queryKey: QueryKey,
  route: Record<string, string | number | undefined> = {},
  query: Record<string, string | number | undefined> = {}
) {
  const [mainKey, otherKeys = {}] = queryKey;

  return [mainKey, { ...otherKeys, ...route, ...query }];
}

/** Handle request errors */
function handleRequestError(error: unknown) {
  if (isAxiosError(error)) {
    // Handle connection errors (no response)
    if (!error.response) {
      if (error.code === 'ERR_CONNECTION_REFUSED' || error.code === 'ERR_NETWORK') {
        throw {
          message: 'Unable to connect to the server. Please check if the backend is running.',
          code: error.code
        };
      }
      throw {
        message: 'Network error occurred. Please check your connection.',
        code: error.code || 'NETWORK_ERROR'
      };
    }

    // Handle HTTP response errors
    const errorData = error.response.data || {
      message: `Server error: ${error.response.status}`,
    };

    // Preserve status code for proper error handling
    throw {
      ...errorData,
      status: error.response.status,
      response: {
        status: error.response.status,
        data: errorData
      }
    };
  }

  if (error instanceof ZodError) {
    logger.error('Validation error', error.format());
  }

  logger.error('Unknown error', error);

  throw error;
}

/* ----------------------------------- GET ---------------------------------- */

interface CreateGetQueryHookArgs<ResponseSchema extends z.ZodType> {
  /** The endpoint for the GET request */
  endpoint: string;
  /** The Zod schema for the response data */
  responseSchema: ResponseSchema;
  /** The query parameters for the react-query hook */
  rQueryParams: Omit<UndefinedInitialDataOptions, 'queryFn' | 'queryKey'> & {
    queryKey: QueryKey;
  };
}

/**
 * Create a custom hook for performing GET requests with react-query and Zod validation
 *
 * @example
 * const useGetUser = createGetQueryHook<typeof userSchema, { id: string }>({
 *   endpoint: '/api/users/:id',
 *   responseSchema: userSchema,
 *   rQueryParams: { queryKey: ['getUser'] },
 * });
 *
 * const { data, error } = useGetUser({ route: { id: 1 } });
 */
export function createGetQueryHook<
  ResponseSchema extends z.ZodType,
  RouteParams extends Record<string, string | number | undefined> = {},
  QueryParams extends Record<string, string | number | undefined> = {},
>({ endpoint, responseSchema, rQueryParams }: CreateGetQueryHookArgs<ResponseSchema>) {
  const queryFn = async (params?: { query?: QueryParams; route?: RouteParams }) => {
    // Global authentication check - exclude authentication endpoints
    const isAuthEndpoint = endpoint.includes('/auth/login') || endpoint.includes('/auth/register');
    if (!isAuthEndpoint) {
      const token = localStorage.getItem('jwt_token');
      if (!token || !token.trim()) {
        throw new Error('Authentication required');
      }
    }

    const url = createUrl(endpoint, params?.query, params?.route);
    return client
      .get(url)
      .then((response) => {
        return responseSchema.parse(response.data);
      })
      .catch((error) => {
        logger.error(`GET ${url} failed`, error);
        return handleRequestError(error);
      });
  };

  return (params?: { query?: QueryParams; route?: RouteParams; enabled?: boolean }) =>
    useQuery({
      ...rQueryParams,
      queryKey: getQueryKey(rQueryParams.queryKey, params?.route, params?.query),
      queryFn: () => queryFn(params),
      // Use enabled from params if provided, otherwise use rQueryParams.enabled, otherwise default to true
      enabled: params?.enabled !== undefined ? params.enabled : (rQueryParams.enabled !== undefined ? rQueryParams.enabled : true),
    }) as UseQueryResult<z.infer<ResponseSchema>>;
}

/* ---------------------------------- POST ---------------------------------- */

interface CreatePostMutationHookArgs<
  BodySchema extends z.ZodType,
  ResponseSchema extends z.ZodType,
> {
  /** The endpoint for the POST request */
  endpoint: string;
  /** The Zod schema for the request body */
  bodySchema: BodySchema;
  /** The Zod schema for the response data */
  responseSchema: ResponseSchema;
  /** The mutation parameters for the react-query hook */
  rMutationParams?: EnhancedMutationParams<z.infer<ResponseSchema>, Error, z.infer<BodySchema>>;
  options?: { isMultipart?: boolean };
}

/**
 * Create a custom hook for performing POST requests with react-query and Zod validation
 *
 * @example
 * const useCreateUser = createPostMutationHook({
 *  endpoint: '/api/users',
 *  bodySchema: createUserSchema,
 *  responseSchema: userSchema,
 *  rMutationParams: { onSuccess: () => queryClient.invalidateQueries('getUsers') },
 * });
 */
export function createPostMutationHook<
  ResponseSchema extends z.ZodType,
  BodySchema extends z.ZodType,
  RouteParams extends Record<string, string | number | undefined> = {},
  QueryParams extends Record<string, string | number | undefined> = {},
>({
  endpoint,
  bodySchema,
  responseSchema,
  rMutationParams,
  options,
}: CreatePostMutationHookArgs<ResponseSchema, BodySchema>) {
  return (params?: { query?: QueryParams; route?: RouteParams }) => {
    const queryClient = useQueryClient();

    const mutationFn = async ({
      variables,
      route,
      query,
    }: {
      variables: z.infer<BodySchema>;
      query?: QueryParams;
      route?: RouteParams;
    }) => {
      // Global authentication check - exclude login and register endpoints
      const isAuthEndpoint = endpoint.includes('/auth/login') || endpoint.includes('/auth/register');
      if (!isAuthEndpoint) {
        const token = localStorage.getItem('jwt_token');
        if (!token || !token.trim()) {
          throw new Error('Authentication required');
        }
      }

      // Combine route parameters from both params and mutation call
      const combinedRoute = { ...params?.route, ...route };
      const combinedQuery = { ...params?.query, ...query };

      const url = createUrl(endpoint, combinedQuery, combinedRoute);

      const config = options?.isMultipart
        ? { headers: { 'Content-Type': 'multipart/form-data' } }
        : undefined;

      return client
        .post(url, bodySchema.parse(variables), config)
        .then((response) => responseSchema.parse(response.data))
        .catch(handleRequestError);
    };

    return useMutation({
      ...rMutationParams,
      mutationFn,
      onSuccess: (data, variables, context) =>
        rMutationParams?.onSuccess?.(data, variables, context, queryClient),
      onError: (error, variables, context) =>
        rMutationParams?.onError?.(error, variables, context, queryClient),
      onSettled: (data, error, variables, context) =>
        rMutationParams?.onSettled?.(data, error, variables, context, queryClient),
    });
  };
}

/* ----------------------------------- PUT ---------------------------------- */

interface CreatePutMutationHookArgs<
  BodySchema extends z.ZodType,
  ResponseSchema extends z.ZodType,
> {
  /** The endpoint for the PUT request */
  endpoint: string;
  /** The Zod schema for the request body */
  bodySchema: BodySchema;
  /** The Zod schema for the response data */
  responseSchema: ResponseSchema;
  /** The mutation parameters for the react-query hook */
  rMutationParams?: EnhancedMutationParams<z.infer<ResponseSchema>, Error, z.infer<BodySchema>>;
  options?: { isMultipart?: boolean };
}

/**
 * Create a custom hook for performing PUT requests with react-query and Zod validation
 *
 * @example
 * const useUpdateUser = createPutMutationHook<typeof updateUserSchema, typeof userSchema, { id: string }>({
 *  endpoint: '/api/users/:id',
 *  bodySchema: updateUserSchema,
 *  responseSchema: userSchema,
 *  rMutationParams: { onSuccess: () => queryClient.invalidateQueries('getUsers') },
 * });
 */
export function createPutMutationHook<
  BodySchema extends z.ZodType,
  ResponseSchema extends z.ZodType,
  RouteParams extends Record<string, string | number | undefined> = {},
  QueryParams extends Record<string, string | number | undefined> = {},
>({
  endpoint,
  bodySchema,
  responseSchema,
  rMutationParams,
  options,
}: CreatePutMutationHookArgs<BodySchema, ResponseSchema>) {
  return (params?: { query?: QueryParams; route?: RouteParams }) => {
    const queryClient = useQueryClient();

    const mutationFn = async ({
      variables,
      route,
      query,
    }: {
      variables: z.infer<BodySchema>;
      query?: QueryParams;
      route?: RouteParams;
    }) => {
      // Global authentication check
      const token = localStorage.getItem('jwt_token');
      if (!token || !token.trim()) {
        throw new Error('Authentication required');
      }

      // Combine route parameters from both params and mutation call
      const combinedRoute = { ...params?.route, ...route };
      const combinedQuery = { ...params?.query, ...query };

      const url = createUrl(endpoint, combinedQuery, combinedRoute);

      const config = options?.isMultipart
        ? { headers: { 'Content-Type': 'multipart/form-data' } }
        : undefined;

      return client
        .put(url, bodySchema.parse(variables), config)
        .then((response) => responseSchema.parse(response.data))
        .catch(handleRequestError);
    };

    return useMutation({
      ...rMutationParams,
      mutationFn,
      onSuccess: (data, variables, context) =>
        rMutationParams?.onSuccess?.(data, variables, context, queryClient),
      onError: (error, variables, context) =>
        rMutationParams?.onError?.(error, variables, context, queryClient),
      onSettled: (data, error, variables, context) =>
        rMutationParams?.onSettled?.(data, error, variables, context, queryClient),
    });
  };
}

/* --------------------------------- DELETE --------------------------------- */

interface CreateDeleteMutationHookArgs<
  TData = unknown,
  TError = Error,
  TVariables = void,
  TContext = unknown,
> {
  /** The endpoint for the DELETE request */
  endpoint: string;
  /** The mutation parameters for the react-query hook */
  rMutationParams?: EnhancedMutationParams<TData, TError, TVariables, TContext>;
}

/**
 * Create a custom hook for performing DELETE requests with react-query
 *
 * @example
 * const useDeleteUser = createDeleteMutationHook<typeof userSchema, { id: string }>({
 *  endpoint: '/api/users/:id',
 *  rMutationParams: { onSuccess: () => queryClient.invalidateQueries('getUsers') },
 * });
 */
export function createDeleteMutationHook<
  ModelSchema extends z.ZodType,
  RouteParams extends Record<string, string | number | undefined> = {},
  QueryParams extends Record<string, string | number | undefined> = {},
>({
  endpoint,
  rMutationParams,
}: CreateDeleteMutationHookArgs<z.infer<ModelSchema>, Error, z.infer<ModelSchema>>) {
  return (params?: { query?: QueryParams; route?: RouteParams }) => {
    const queryClient = useQueryClient();
    const baseUrl = createUrl(endpoint, params?.query, params?.route);

    const mutationFn = async ({
      model,
      route,
      query,
    }: {
      model: z.infer<ModelSchema>;
      query?: QueryParams;
      route?: RouteParams;
    }) => {
      // Global authentication check
      const token = localStorage.getItem('jwt_token');
      if (!token || !token.trim()) {
        throw new Error('Authentication required');
      }

      // Combine route parameters from both params and mutation call
      const combinedRoute = { ...params?.route, ...route };
      const combinedQuery = { ...params?.query, ...query };

      const url = createUrl(endpoint, combinedQuery, combinedRoute);

      return client
        .delete(url, { data: model })
        .then((response) => response.data)
        .catch(handleRequestError);
    };

    return useMutation({
      ...rMutationParams,
      mutationFn,
      onSuccess: (data, variables, context) =>
        rMutationParams?.onSuccess?.(data, variables, context, queryClient),
      onError: (error, variables, context) =>
        rMutationParams?.onError?.(error, variables, context, queryClient),
      onSettled: (data, error, variables, context) =>
        rMutationParams?.onSettled?.(data, error, variables, context, queryClient),
    });
  };
}

/* ------------------------------- PAGINATION ------------------------------- */

export type PaginationParams = {
  page?: number;
  limit?: number;
};

export function usePagination(params?: PaginationParams) {
  const [page, setPage] = useState(params?.page ?? 1);
  const [limit, setLimit] = useState(params?.limit ?? 15);

  const onChangeLimit = (value: number) => {
    setLimit(value);
    setPage(1);
  };

  return { page, limit, setPage, setLimit: onChangeLimit };
}

export const PaginationMetaSchema = z.object({
  total: z.number().int().min(0),
  perPage: z.number().int().positive(),
  currentPage: z.number().int().positive().nullable(),
  lastPage: z.number().int().positive(),
  firstPage: z.number().int().positive(),
  firstPageUrl: z.string(),
  lastPageUrl: z.string(),
  nextPageUrl: z.string().nullable(),
  previousPageUrl: z.string().nullable(),
});

export type PaginationMeta = z.infer<typeof PaginationMetaSchema>;

interface CreatePaginationQueryHookArgs<DataSchema extends z.ZodType> {
  /** The endpoint for the GET request */
  endpoint: string;
  /** The Zod schema for the data attribute in response */
  dataSchema: DataSchema;
  /** The query parameters for the react-query hook */
  rQueryParams: Omit<UndefinedInitialDataOptions, 'queryFn' | 'queryKey'> & {
    queryKey: QueryKey;
  };
}

export type SortableQueryParams = {
  sort?: `${string}:${'asc' | 'desc'}`;
};

/**
 * Create a custom hook for performing paginated GET requests with react-query and Zod validation
 *
 * @example
 * const useGetUsers = createPaginatedQueryHook<typeof userSchema>({
 *  endpoint: '/api/users',
 *  dataSchema: userSchema,
 *  queryParams: { queryKey: 'getUsers' },
 * });
 */
export function createPaginationQueryHook<
  DataSchema extends z.ZodType,
  QueryParams extends Record<string, string | number | undefined> = SortableQueryParams,
  RouteParams extends Record<string, string | number | undefined> = {},
>({ endpoint, dataSchema, rQueryParams }: CreatePaginationQueryHookArgs<DataSchema>) {
  const queryFn = async (params: {
    query?: QueryParams & PaginationParams;
    route?: RouteParams;
  }) => {
    const url = createUrl(endpoint, params?.query, params?.route);

    const schema = z.object({
      data: dataSchema.array(),
      meta: PaginationMetaSchema,
    });

    return client
      .get(url)
      .then((response) => schema.parse(response.data))
      .catch(handleRequestError);
  };

  return (params?: { query: QueryParams & PaginationParams; route?: RouteParams }) => {
    const query = { page: 1, limit: 25, ...params?.query } as unknown as QueryParams;
    const route = params?.route ?? ({} as RouteParams);

    return useQuery({
      ...rQueryParams,
      queryKey: getQueryKey(rQueryParams.queryKey, route, query),
      queryFn: () => queryFn({ query, route }),
    }) as UseQueryResult<{ meta: PaginationMeta; data: z.infer<DataSchema>[] }>;
  };
}
