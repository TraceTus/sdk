import type { TraceTusError } from "./errors.js";
/**
 * The client's types, derived from the generated document and from nothing
 * else.
 *
 * openapi-typescript keys its `operations` interface by `operationId`, and the
 * API names every operation `resource.action` (its own contract test
 * holds it to that). Those two facts are what let the whole client be typed
 * here, once, instead of a signature per endpoint: a route added to the API
 * appears in `tracetus.<resource>.<action>` on the next generation, with its
 * own input and output types, and this file does not change.
 */
import type { operations } from "./generated/openapi.js";

export type OperationId = keyof operations & string;

/** The part before the dot: `records` in `records.create`. */
export type ResourceOf<Id extends string> = Id extends `${infer Resource}.${string}`
  ? Resource
  : never;

/** The part after the dot: `create` in `records.create`. */
export type ActionOf<Id extends string> = Id extends `${string}.${infer Action}` ? Action : never;

type JsonContent<Response> = Response extends { content: { "application/json": infer Body } }
  ? Body
  : never;

type TextContent<Response> = Response extends { content: { "text/plain": infer Body } }
  ? Body
  : never;

/** 200 and 201 are the only answers the API calls success. */
type SuccessStatus = 200 | 201;

type SuccessResponse<Id extends OperationId> =
  operations[Id]["responses"][keyof operations[Id]["responses"] & SuccessStatus];

export type DataOf<Id extends OperationId> =
  | JsonContent<SuccessResponse<Id>>
  | TextContent<SuccessResponse<Id>>;

type BodyOf<Id extends OperationId> = operations[Id] extends {
  requestBody: { content: { "application/json": infer Body } };
}
  ? Body
  : never;

type PathOf<Id extends OperationId> = NonNullable<operations[Id]["parameters"]["path"]>;

type QueryOf<Id extends OperationId> = NonNullable<operations[Id]["parameters"]["query"]>;

/**
 * An intersection with `unknown` disappears, so an operation with no body gets
 * no `body` key at all rather than an optional one it must not have.
 */
type BodyPart<Id extends OperationId> = [BodyOf<Id>] extends [never]
  ? unknown
  : { body: BodyOf<Id> };

type PathPart<Id extends OperationId> = [PathOf<Id>] extends [never]
  ? unknown
  : { path: PathOf<Id> };

/**
 * `query` is required only when the route has a query parameter that is itself
 * required. A route whose whole query is optional — a cursor listing, where no
 * cursor means the first page — is callable with no argument at all, and
 * asking for `query: {}` would be noise the caller has to write.
 */
type QueryPart<Id extends OperationId> = [QueryOf<Id>] extends [never]
  ? unknown
  : Record<string, never> extends QueryOf<Id>
    ? { query?: QueryOf<Id> }
    : { query: QueryOf<Id> };

/**
 * Headers the caller may add. `Idempotency-Key` is not asked for here even
 * though the document requires it on a `POST`: the client makes one per call
 * and keeps it across the retries of that call, which is the whole point. A
 * caller that has its own key may still pass it, and then that one is used.
 */
interface HeaderPart {
  headers?: Readonly<Record<string, string>>;
}

export type RequestInput<Id extends OperationId> = BodyPart<Id> &
  PathPart<Id> &
  QueryPart<Id> &
  HeaderPart;

/** True when nothing in the input is required, so the argument may be left out. */
type NothingRequired<Input> = RequiredKeysOf<Input> extends never ? true : false;

type RequiredKeysOf<Input> = {
  [Key in keyof Input]-?: Record<string, never> extends Pick<Input, Key> ? never : Key;
}[keyof Input];

export interface CallOptions {
  /** Milliseconds for one attempt. Overrides the client's own. */
  timeoutMs?: number;
  /** Attempts in total, the first one included. Overrides the client's own. */
  attempts?: number;
  /** A signal of the caller's, honoured alongside the timeout. */
  signal?: AbortSignal;
}

/**
 * Exactly one of `data` and `error`, so a check of one narrows the other: a
 * caller that returns early on `error` has a defined `data` afterwards, and the
 * compiler knows it.
 */
export type Result<Data> =
  | { data: Data; error?: undefined; response: Response }
  | { data?: undefined; error: TraceTusError; response: Response | undefined };

export type Call<Id extends OperationId> = NothingRequired<RequestInput<Id>> extends true
  ? (input?: RequestInput<Id>, options?: CallOptions) => Promise<Result<DataOf<Id>>>
  : (input: RequestInput<Id>, options?: CallOptions) => Promise<Result<DataOf<Id>>>;

/**
 * The client's shape: one namespace per resource, one method per action, built
 * from the operation names themselves.
 */
export type TraceTusClient = {
  [Resource in ResourceOf<OperationId>]: {
    [Id in OperationId as Id extends `${Resource}.${infer Action}` ? Action : never]: Call<Id>;
  };
};
