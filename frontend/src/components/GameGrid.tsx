import Grid from '@mui/material/Grid';
import React from 'react';
import {Game} from '../types/game';
import {GameCard} from './GameCard';

type Props = {
  games: Game[];
  onGameClick: (game: Game) => void;
  onFavorite: (game: Game) => void;
};

export const GameGrid: React.FC<Props> = ({games, onGameClick, onFavorite}) => {
  if (games.length === 0) {
    return (
      <Grid container spacing={2} justifyContent="center">
        <h2>Nothing found</h2>
      </Grid>
    )
  }
  return (
    <Grid container spacing={2}>
      {games.map((game) => (
        <Grid size={{xs: 12, sm: 6, md: 4}} key={game.project}>
          <GameCard
            game={game}
            onClick={() => onGameClick(game)}
            onFavorite={() => onFavorite(game)}
          />
        </Grid>
      ))}
    </Grid>
  )
};

export {};
