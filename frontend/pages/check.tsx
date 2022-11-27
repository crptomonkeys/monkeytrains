import { Grid } from '@mui/material';
import Container from '@mui/material/Container';
// import MainCard from '../components/MainCard';
import DarkCard from '../components/cards/DarkCard'
import LightCard from '../components/cards/LightCard'

import humanizeDuration from "humanize-duration";

import Link from '../src/Link';
import axios from 'axios';
import useSWR from 'swr';
import Image from 'next/image'
import { Typography } from '@mui/material';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import HistoryIcon from '@mui/icons-material/History';
import CasinoIcon from '@mui/icons-material/Casino';
import { Box, Stack, Button } from '@mui/material';
import { useState } from 'react';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import {DateTime} from 'luxon';

import CircularProgress from '@mui/material/CircularProgress';

import TableTemplate from '../components/TableTemplate';

function addMinutes(date:Date, minutes:number) {
    return DateTime.fromJSDate(date).plus({minutes}).toJSDate()
}

function getTypeNamed(type:string){
  if (type=="roading"){
    return "Raffle"
  }
  if (type=="targetmining"){
    return "Target mining"
  }
}

export default function PDash() {
  const [railroader, setRailroader] = useState("");
  const { data: runs } = useSWR<TrainsApiResponse, Error>(
    [
      'https://history.api.trains.cards/logrun',
      { params: { railroader: railroader } },
    ],
    (url, options) => axios.get(url, options).then((res) => res.data),
    {refreshInterval:50000, }
  );
  const { data:db } = useSWR(
    ['https://trains.api.cryptomonkeys.cc/get_personal'],
    (url) => axios.get(url).then((res) => res.data),
    {refreshInterval:60000, }
  );
  const { data: drops } = useSWR<DropsApiResponse, Error>(
    ['https://trains.api.cryptomonkeys.cc/drops', { params: { before: '', after: '',limit: 10000 } }],
    (url, options) => axios.get(url, options).then((res) => res.data),
    {refreshInterval:60000, }
  );

  if (!runs || !db) return (
    <Container>
      <div style={{display: 'flex', justifyContent: 'center'}}>
      <CircularProgress />
      </div>
    </Container>
            
  );
  if (railroader == "") return (
    <Container>
      <Grid item xs={12} md={12}>
      <Autocomplete
        freeSolo
        id="miner"
        disableClearable
        options={db.cmcs}
        onChange={(event, newValue:string) => {
          setRailroader(newValue);
        }}
        renderInput={(params) => (
          <TextField
          required
            {...params}
            label="Your Wallet address"
            InputProps={{
              ...params.InputProps,
              type: 'search',
            }}
          />
        )}
      />
      </Grid>
    </Container>
    
            
  );
  
  const date = Date.now();
  const connected = db.cmcs.includes(railroader);
  let con_card = <DarkCard icon={<Image src="/cmc.png" alt="target Logo" width={32} height={32} />} label={"monkeyconnected?"} value={"Yes!"} />;
  if (!connected){
    con_card = <LightCard icon={<Image src="/cmc.png" alt="target Logo" width={32} height={32} />} label={"monkeyconnected?"} value={<Button variant="contained" color="success" size='large' href="https://connect.cryptomonkeys.cc">Signup</Button>} />;
  }
  let cd = "not on CD";
  const cdif = db.cds[railroader];
  if (cdif){
    const dat = new Date(Date.parse(cdif+"Z"));
    const ndir = addMinutes(dat,4320);
    if (ndir.getTime() > date){

      cd = humanizeDuration(date-ndir.getTime(),{ round: true, units: ["d", "h", "m"] });
    }
  }
  let eligible = <LightCard icon={<CasinoIcon/>} label={"eligible for next raffle?"} value={"No!"} />;
  if (runs.data.length > 0){
    const cur = new Date();
    const cut = DateTime.fromJSDate(cur).minus(60*60*1000).toJSDate();
    const lig = new Date(Date.parse(runs.data[0].block_time+"Z"));
    if (Date.parse(db.db.last_elec+"Z") < Date.parse(runs.data[0].block_time+"Z")){
      eligible = <DarkCard icon={<CasinoIcon/>} label={"eligible for next raffle?"} value={"Yes!"} />;
    }
  }
  let drops_clean : Drop[] = [];
  if (drops){
    drops_clean = drops.data.reduce((drops_clean,drop) => {
      if (drop.winner.includes(railroader)) {
        drops_clean.push(drop);
      }
      return drops_clean;
    }, []);
  }
   
  return (
    <Container>
      <Box
          sx={{
            bgcolor: 'background.paper',
            pt: 8,
            pb: 6,
          }}
        >
          <Container maxWidth="sm">
            <Typography
              component="h2"
              variant="h2"
              align="center"
              color="text.primary"
              gutterBottom
            >
              Hi {railroader}!
            </Typography>
          </Container>
        </Box>
      
      <br/>
      
      
       <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
        {con_card}
      </Grid>
       <Grid item xs={12} md={6}>
          <DarkCard icon={<HistoryIcon/>} label={"Cooldown duration for raffle"} value={cd} />
      </Grid>
      
      <Grid item xs={12} md={3}>
        {eligible}
      </Grid>
         <br/>
      <Grid item xs={12} md={12}>
      <Typography variant='h5'>Your latest wins</Typography>
        </Grid>
        <br/>
      <TableTemplate
        names={['When?', 'Type', 'Winner', 'Status', 'Transaction']}
        data={drops_clean?.map((row, i) => (
          <TableRow key={i} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
            <TableCell>{humanizeDuration(Date.now()-Date.parse(row.issue_time+"Z"),{ round: true , conjunction: " and "})} ago</TableCell>
            <TableCell>{getTypeNamed(row.type)}</TableCell>
            <TableCell>{row.winner.join(", ")}</TableCell>
            <TableCell>{row.state}</TableCell>
            <TableCell>
              <Link sx={{  textDecoration: 'none'}} href={`https://wax.bloks.io/transaction/${row.trx_id}`}>
                <Button variant='outlined'>bloks.io</Button>
              </Link>
            </TableCell>
          </TableRow>
        ))}
      />
      
      <br/>
       <br/>
      <Grid item xs={12} md={12}>
      <Typography variant='h5'>Your latest runs</Typography>
        </Grid>
        <br/>
      <TableTemplate
        names={['When?', 'Who?', 'Reward', 'Station', 'Station owner']}
        data={runs?.data.map((row, i) => (
          <TableRow key={i} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
            <TableCell>{humanizeDuration(date-Date.parse(row.block_time+"Z"),{ round: true })} ago</TableCell>
            <TableCell>{row.railroader}</TableCell>
            <TableCell>{row.railroader_reward}</TableCell>
            <TableCell>{row.arrive_station}</TableCell>
            <TableCell>{row.station_owner}</TableCell>
          </TableRow>
        ))}
        />
       
      </Grid>
      
    </Container>
  );
}
