import React from 'react';
import { Paper, Typography, IconButton, Link } from '@mui/material';
import PinDropIcon from '@mui/icons-material/PinDrop';
import { Game } from '../types/game';
import { GameThumbnail } from './GameThumbnail';

type Props = {
  game: Game;
  onGameClick: (game: Game) => void;
  onFavorite: (game: Game) => void;
  isFavorite: boolean;
  ref?: React.Ref<HTMLDivElement>;
};

export const GameCard: React.FC<Props> = ({ game, onGameClick, onFavorite, isFavorite, ref }) => {
  const url = `${process.env.REACT_APP_API_URL}/game/${game.project}`;
  const handleGameClick = () => { onGameClick(game) };
  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFavorite(game);
  };
  return (
    <Paper sx={{ p: 2, position: 'relative' }} ref={ref}>
      <Typography variant="h6">{game.project}</Typography>
      <div onClick={handleGameClick} style={{ cursor: 'pointer' }}>
        <GameThumbnail
          name={game.project}
          baseUrl={url}
          key={game.project}
        />
      </div>
      <Typography variant="body2">Opened {game.num_opens} times</Typography>
      <Typography variant="body2">
        Created: {new Date(game.date_added).toLocaleDateString()}
      </Typography>
      <Typography variant="body2">
        Last Edited: {new Date(game.date_modified).toLocaleDateString()}
      </Typography>
      <Typography>
        <Link href={url} target="_blank">
          Open in new tab
        </Link>
      </Typography>
      <Link href={game.github_url} target="_blank" rel="noopener noreferrer">
        View on GitHub
      </Link>
      <IconButton
        size="small"
        sx={{ position: 'absolute', top: 8, right: 8, color: isFavorite ? 'orange' : 'inherit' }}
        onClick={handleFavoriteClick}
      >
        <PinDropIcon />
      </IconButton>
    </Paper>
  );
};
