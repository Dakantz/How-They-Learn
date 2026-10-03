/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

import type {
  GradCamResponse,
  HTTPValidationError,
  MetaResponse,
  PredictionsResponse,
  Sample,
} from "./data-contracts";
import { HttpClient } from "./http-client";
import type { RequestParams } from "./http-client";

export class Api<
  SecurityDataType = unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @name MetaApiMetaGet
   * @summary Meta
   * @request GET:/api/meta
   */
  metaApiMetaGet = (params: RequestParams = {}) =>
    this.request<MetaResponse, any>({
      path: `/api/meta`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @name SamplesApiSamplesGet
   * @summary Samples
   * @request GET:/api/samples
   */
  samplesApiSamplesGet = (params: RequestParams = {}) =>
    this.request<Sample[], any>({
      path: `/api/samples`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @name PredictionsApiPredictionsIndexGet
   * @summary Predictions
   * @request GET:/api/predictions/{index}
   */
  predictionsApiPredictionsIndexGet = (
    index: number,
    params: RequestParams = {},
  ) =>
    this.request<PredictionsResponse, HTTPValidationError>({
      path: `/api/predictions/${index}`,
      method: "GET",
      format: "json",
      ...params,
    });
  /**
   * No description
   *
   * @name GradcamApiGradcamGet
   * @summary Gradcam
   * @request GET:/api/gradcam
   */
  gradcamApiGradcamGet = (
    query: {
      /** Index */
      index: number;
      /** Epoch A */
      epoch_a: number;
      /** Epoch B */
      epoch_b: number;
    },
    params: RequestParams = {},
  ) =>
    this.request<GradCamResponse, HTTPValidationError>({
      path: `/api/gradcam`,
      method: "GET",
      query: query,
      format: "json",
      ...params,
    });
}
