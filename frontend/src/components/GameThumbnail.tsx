import { CircularProgress } from '@mui/material';
import React, { useState } from 'react';
import BrokenImageIcon from '@mui/icons-material/BrokenImage';

type Props = {
  thumbUrl: string;
};

export const GameThumbnail: React.FC<Props> = ({ thumbUrl }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div
        style={{
          width: '100%',
          height: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: 8,
        }}
      >
        <BrokenImageIcon color="error" sx={{ opacity: 0.4, fontSize: 96 }} />
      </div>
    );
  }

  return (
    <>
      {!loaded && (
        <div
          style={{
            width: '100%',
            height: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginTop: 8,
          }}
        >
          <CircularProgress size={40} color="primary" />
        </div>
      )}
      <img
        src={thumbUrl}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        style={{
          display: loaded ? 'block' : 'none',
          width: '100%',
          height: 200,
          border: 'none',
          pointerEvents: 'none',
          marginTop: 8,
          backgroundColor: '#fff',
          overflow: 'hidden',
        }}
      />
    </>
  );
};
