import React from 'react';
import {Paper, Typography, IconButton, Link} from '@mui/material';
import PinDropIcon from '@mui/icons-material/PinDrop';
import {Game} from '../types/game';
import {Container} from '@mui/system';

type Props = {
  game: Game;
  onClick: () => void;
  onFavorite: () => void;
};

export const GameCard: React.FC<Props> = ({game, onClick, onFavorite}) => {
  let randomSeed = Math.floor(Math.random() * 1000);
  let url = `${process.env.REACT_APP_API_URL}/api/game/${game.project}?seed=${randomSeed}`;
  return (
    <Paper sx={{p: 2, position: 'relative'}}>
      <Typography variant="h6">{game.project}</Typography>
      <Typography variant="body2">Created: {new Date(game.date_added).toLocaleDateString()}</Typography>
      <Typography variant="body2">
        Last Edited: {new Date(game.date_modified).toLocaleDateString()}
      </Typography>
      <Typography >
        <Link
          href={url}
          target="_blank"
        >
          Open in new tab
        </Link>
      </Typography>
      <div
        onClick={onClick}
        style={{cursor: 'pointer'}}
      >
        <iframe
          src={url}
          title={`${game.project} preview`}
          style={{
            width: '100%',
            height: 200,
            border: 'none',
            pointerEvents: 'none',
            marginTop: 8,
            backgroundColor: '#fff', // Ensure a white background
          }}
        />
      </div>
      <Link
        href={game.github_url}
        target="_blank"
        rel="noopener noreferrer"
      >
        View on GitHub
      </Link>
      <IconButton
        size="small"
        sx={{position: 'absolute', top: 8, right: 8}}
        onClick={(e) => {
          e.stopPropagation();
          onFavorite();
        }}
      >
        <PinDropIcon />
      </IconButton>
    </Paper >
  )
};
