import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import axios from 'axios';
import humanizeDuration from "humanize-duration";
import useSWR from 'swr';
import TableTemplate from './TableTemplate';

import CheckIcon from '@mui/icons-material/Check';


function chooseTick(connected:Set<string>,miner:string){
  if (connected.has(miner)){
    return <CheckIcon/>
  }
}
export default function RunsTable() {
  const { data: mines } = useSWR<TrainsApiResponse, Error>(
    [
      'https://history.api.trains.cards/logrun',
      { params: { limit: 100 } },
    ],
    (url, options) => axios.get(url, options).then((res) => res.data),
    {refreshInterval:1000, }
  );
  const { data:cmcs } = useSWR<CMCApiResponse, Error>(
    ['https://mine.api.cmstats.net/cmc_list'],
    (url) => axios.get(url).then((res) => res.data),
    {refreshInterval:600000, }
  );
  let monkeyconnected = new Set("");
  if (cmcs){
    monkeyconnected = new Set(cmcs.data);
  }
  const date = Date.now();
  
  return (
    <>
      <TableTemplate
        names={['CMC?','When?', 'Who?', 'Reward', 'Station', 'Station owner']}
        data={mines?.data.map((row, i) => (
          <TableRow key={i} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
            <TableCell>{chooseTick(monkeyconnected,row.railroader)}</TableCell>
            <TableCell>{humanizeDuration(date-Date.parse(row.block_time+"Z"),{ round: true })} ago</TableCell>
            <TableCell>{row.railroader}</TableCell>
            <TableCell>{row.railroader_reward}</TableCell>
            <TableCell>{row.arrive_station}</TableCell>
            <TableCell>{row.station_owner}</TableCell>
          </TableRow>
        ))}
      />
    </>
  );
}
