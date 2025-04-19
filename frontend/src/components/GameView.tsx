import React from 'react';
import { Paper, IconButton, Typography, Box } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { Game } from '../types/game';

type Props = {
  game: Game;
  onBack: () => void;
};

export const GameView: React.FC<Props> = ({ game, onBack }) => (
  <Paper sx={{ p: 2, position: 'relative', minHeight: '80vh' }}>
    <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
      <IconButton
        onClick={() => window.open(`${process.env.REACT_APP_API_URL}/game/${game.project}`, '_blank')}
      >
        <OpenInNewIcon />
      </IconButton>
    </Box>
    <Box sx={{ position: 'absolute', bottom: 16, left: 16 }}>
      <IconButton onClick={onBack}>
        <ArrowBackIcon />
      </IconButton>
    </Box>
    <Typography variant="h4" sx={{ mb: 2 }}>
      {game.project}
    </Typography>
    <iframe
      src={`${process.env.REACT_APP_API_URL}/game/${game.project}`}
      title={game.project}
      style={{ width: '100%', height: '70vh', border: 'none', backgroundColor: '#fff' }}
      sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-modals allow-pointer-lock"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    />
  </Paper>
);
