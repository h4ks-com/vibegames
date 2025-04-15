import React from 'react';
import {Paper, IconButton, Typography} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import {Game} from '../types/game';

type Props = {
  game: Game;
  onBack: () => void;
};

export const GameView: React.FC<Props> = ({game, onBack}) => (
  <Paper sx={{p: 2, position: 'relative', minHeight: '80vh'}}>
    <IconButton onClick={onBack} sx={{position: 'absolute', bottom: 16, left: 16}}>
      <ArrowBackIcon />
    </IconButton>
    <Typography variant="h4" sx={{mb: 2}}>
      {game.project}
    </Typography>
    <iframe
      src={`${process.env.REACT_APP_API_URL}/game/${game.project}`}
      title={game.project}
      style={{width: '100%', height: '70vh', border: 'none', pointerEvents: 'none', backgroundColor: '#fff'}}
      sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
    />
  </Paper>
);
