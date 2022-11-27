interface BaseApiResponse {
  query_time: number;
  count: number;
}

interface Run {
  railroader: string;
  train_name: string;
  railroader_reward: number;
  trx_id: string;
  station_owner: string;
  id: number;
  arrive_station: string;
  block_time: string;
  block_timestamp: number;
}

interface TrainsApiResponse extends BaseApiResponse {
  data: Run[];
}

interface Drop {
  issue_time: string;
  type: string;
  winner: string[];
  trx_id: string;
  state: string;
}

interface DropsApiResponse extends BaseApiResponse {
  data: Drop[];
}

interface CMCApiResponse extends BaseApiResponse {
  data: string[];
}
